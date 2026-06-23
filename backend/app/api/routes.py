from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_ingestion import DataIngestionService
from app.models.schemas import DatasetOverviewResponse, DataQualityResponse
from app.core.state import active_sessions
import uuid
import gc
import math
import pandas as pd
import time

router = APIRouter()

def sweep_expired_sessions():
    now = time.time()
    expired = [sid for sid, data in active_sessions.items() if isinstance(data, dict) and now - data.get("last_accessed", now) > 3600]
    for sid in expired:
        del active_sessions[sid]
    if expired:
        gc.collect()

def get_df_from_session(session_id: str):
    session_data = active_sessions.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if isinstance(session_data, dict):
        session_data["last_accessed"] = time.time()
        if "history" in session_data and len(session_data["history"]) > 0:
            return session_data["history"][-1]
        elif "raw" in session_data:
            return session_data.get("cleaned") if session_data.get("cleaned") is not None else session_data.get("raw")
            
    return session_data

@router.post("/upload", response_model=dict)
async def upload_dataset(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = DataIngestionService.parse_file(content, file.filename)
        
        sweep_expired_sessions()
        
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "history": [df],
            "history_logs": ["Uploaded dataset"],
            "raw": df, 
            "cleaned": df, 
            "last_accessed": time.time()
        }
        
        from app.services.metadata_manager import MetadataManager
        active_sessions[session_id]["metadata_cache"] = MetadataManager.compute_all_masks(df)
        
        overview = DataIngestionService.get_overview(df, file.filename, len(content))
        
        return {
            "session_id": session_id,
            "overview": overview
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in active_sessions:
        # 1. Delete reference from state dictionary
        del active_sessions[session_id]
        # 2. Force Python's Garbage Collector to instantly free the RAM to the OS
        gc.collect()
        return {"message": "Session and all associated data permanently deleted from memory."}
    return {"message": "Session not found."}

@router.get("/quality/{session_id}")
async def get_data_quality(session_id: str):
    df = get_df_from_session(session_id)
    try:
        from app.services.data_quality import DataQualityService
        from app.agents.insight_agent import InsightAgent
        
        cache = active_sessions[session_id].get("metadata_cache") if session_id in active_sessions and isinstance(active_sessions[session_id], dict) else None
        quality_report = DataQualityService.analyze_quality(df, masks_cache=cache)
        
        agent = InsightAgent()
        health_report = agent.generate_health_report(quality_report)
        quality_report["ai_health_report"] = health_report
        
        return quality_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import Optional

class TargetedCleanRequest(BaseModel):
    issue: str
    columns: list
    method: str = ""
    custom_value: Optional[str] = None

@router.post("/clean/{session_id}/preview")
async def preview_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        session_data = active_sessions.get(session_id, {})
        cache = session_data.get("metadata_cache")
        
        affected_idx = None
        if cache:
            cols = request.columns if request.columns and len(request.columns) > 0 and request.columns[0] != 'all' else df.columns
            if request.issue == 'Missing Values':
                affected_idx = df.index[cache["missing_mask"][cols].any(axis=1)]
            elif request.issue == 'Empty Cells':
                affected_idx = df.index[cache["empty_mask"][cols].any(axis=1)]
            elif request.issue == 'Outliers':
                affected_idx = df.index[cache["outlier_mask"][cols].any(axis=1)]
            elif request.issue in ['Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates']:
                affected_idx = df.index[cache["global_dups"]]
                
        if affected_idx is None or len(affected_idx) == 0:
            affected_idx = df.index
            
        # Sample at most 100 affected rows
        affected_idx = affected_idx[:100]
        
        # Build preview only for affected rows
        from app.services.data_cleaning import DataCleaningService
        df_subset = df.loc[affected_idx].copy()
        
        # Try to clean just the subset to save time if possible (if row-independent)
        # For duplicates/outliers, cleaning subset doesn't work well (depends on global distribution)
        # So we clean full df, but we only to_dict the subset!
        preview_df = DataCleaningService.apply_targeted_cleaning(df, request.issue, request.columns, request.method, request.custom_value)
        
        original_preview = df.loc[affected_idx].where(pd.notnull(df.loc[affected_idx]), None).to_dict(orient="records")
        
        # For cleaned_preview, some rows might have been dropped
        cleaned_idx = [i for i in affected_idx if i in preview_df.index]
        cleaned_preview = preview_df.loc[cleaned_idx].where(pd.notnull(preview_df.loc[cleaned_idx]), None).to_dict(orient="records")
        
        return {"original_preview": original_preview, "cleaned_preview": cleaned_preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clean/{session_id}/apply")
async def apply_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        from app.services.data_cleaning import DataCleaningService
        cleaned_df = DataCleaningService.apply_targeted_cleaning(df, request.issue, request.columns, request.method, request.custom_value)
        
        if session_id in active_sessions and isinstance(active_sessions[session_id], dict):
            # Only keep raw and latest cleaned to optimize memory
            if "raw" in active_sessions[session_id]:
                active_sessions[session_id]["history"] = [active_sessions[session_id]["raw"], cleaned_df]
                if len(active_sessions[session_id].get("history_logs", [])) < 2:
                    active_sessions[session_id]["history_logs"] = ["Initial state"]
            
            # Format action description nicely
            cols_str = "all columns" if not request.columns or request.columns == ['all'] else ", ".join(str(c) for c in request.columns)
            action_desc = f"{request.method} applied to {cols_str} for {request.issue}"
            active_sessions[session_id]["history_logs"].append(action_desc)
            
            active_sessions[session_id]["cleaned"] = cleaned_df
            
            # Update cache incrementally
            from app.services.metadata_manager import MetadataManager
            cache = active_sessions[session_id].get("metadata_cache")
            if cache:
                active_sessions[session_id]["metadata_cache"] = MetadataManager.update_masks(cleaned_df, cache, request.issue, request.columns)
            else:
                active_sessions[session_id]["metadata_cache"] = MetadataManager.compute_all_masks(cleaned_df)
                
            # Clear intermediate variables
            gc.collect()
            
        rows_affected = len(df) - len(cleaned_df)
        
        from app.services.data_quality import DataQualityService
        # Incrementally update quality
        cache = active_sessions[session_id].get("metadata_cache") if session_id in active_sessions and isinstance(active_sessions[session_id], dict) else None
        new_quality = DataQualityService.analyze_quality(cleaned_df, masks_cache=cache)
            
        return {"message": "Data cleaned successfully", "rows_affected": rows_affected, "new_quality": new_quality}
    except Exception as e:
        import traceback
        with open('apply_error_log.txt', 'w') as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clean/{session_id}/undo")
async def undo_cleaning(session_id: str):
    session_data = active_sessions.get(session_id)
    if not session_data or not isinstance(session_data, dict):
        raise HTTPException(status_code=404, detail="Session not found")
        
    if "raw" in session_data:
        # Revert to raw
        session_data["cleaned"] = session_data["raw"]
        session_data["history"] = [session_data["raw"]]
        session_data["history_logs"] = ["Reverted to original state"]
        
        from app.services.metadata_manager import MetadataManager
        session_data["metadata_cache"] = MetadataManager.compute_all_masks(session_data["raw"])
        gc.collect()
        return {"message": "Reverted to original state successfully"}
    else:
        raise HTTPException(status_code=400, detail="Nothing to undo")

@router.get("/clean/{session_id}/history")
async def get_cleaning_history(session_id: str):
    session_data = active_sessions.get(session_id)
    if not session_data or not isinstance(session_data, dict):
        raise HTTPException(status_code=404, detail="Session not found")
        
    logs = session_data.get("history_logs", [])
    return {"history": logs}

@router.post("/clean/{session_id}/recommend")
async def recommend_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        from app.agents.cleaning_agent import CleaningAgent
        import pandas as pd
        agent = CleaningAgent()
        
        stats = {}
        for col in request.columns:
            if col in df.columns:
                col_stats = {
                    "type": str(df[col].dtype),
                    "missing": int(df[col].isna().sum()),
                    "unique": int(df[col].nunique())
                }
                if request.issue == 'Outliers' and pd.api.types.is_numeric_dtype(df[col]):
                    s = df[col].dropna()
                    if len(s) > 0:
                        q1 = s.quantile(0.25)
                        q3 = s.quantile(0.75)
                        iqr = q3 - q1
                        lower = q1 - 1.5 * iqr
                        upper = q3 + 1.5 * iqr
                        outliers = ((s < lower) | (s > upper)).sum()
                        col_stats["outlier_count"] = int(outliers)
                        col_stats["outlier_percentage"] = round((int(outliers) / len(s)) * 100, 2)
                        col_stats["iqr_lower_bound"] = float(lower)
                        col_stats["iqr_upper_bound"] = float(upper)
                stats[col] = col_stats
        
        rec = agent.recommend(request.issue, ", ".join(request.columns), stats)
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clean/{session_id}/preview")
async def preview_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        from app.services.data_cleaning import DataCleaningService
        cleaned_df = DataCleaningService.apply_targeted_cleaning(df, request.issue, request.columns, request.method, request.custom_value)
        
        rows_removed = len(df) - len(cleaned_df)
        values_changed = 0
        
        if rows_removed == 0 and request.columns and request.columns[0] != 'all':
            for col in request.columns:
                if col in df.columns and col in cleaned_df.columns:
                    mask = df[col].astype(str) != cleaned_df[col].astype(str)
                    values_changed += int(mask.sum())
                    
        if rows_removed > 0:
            original_preview = df.head(100).fillna("").to_dict(orient="records")
            cleaned_preview = cleaned_df.head(100).fillna("").to_dict(orient="records")
            affected = rows_removed
        else:
            diff_mask = pd.Series(False, index=df.index)
            if request.columns and request.columns[0] != 'all':
                for col in request.columns:
                    if col in df.columns and col in cleaned_df.columns:
                        diff_mask = diff_mask | (df[col].astype(str) != cleaned_df[col].astype(str))
            
            diff_indices = df[diff_mask].head(100).index
            
            if len(diff_indices) == 0:
                diff_indices = df.head(5).index
                
            original_preview = df.loc[diff_indices].fillna("").to_dict(orient="records")
            cleaned_preview = cleaned_df.loc[diff_indices].fillna("").to_dict(orient="records")
            affected = len(diff_indices)
            
        return {
            "original_preview": original_preview,
            "cleaned_preview": cleaned_preview,
            "metrics": {
                "rows_affected": affected,
                "values_changed": values_changed,
                "rows_removed": rows_removed,
                "estimated_quality_improvement": "+2.5%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/{session_id}")
async def get_visualizations(session_id: str):
    df = get_df_from_session(session_id)
    try:
        from app.agents.visualization_agent import VisualizationAgent
        agent = VisualizationAgent()
        charts_config = agent.generate_visualizations(df)
        
        return {"visualizations": charts_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{session_id}")
async def get_insights(session_id: str):
    df = get_df_from_session(session_id)
    try:
        from app.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        insights = agent.generate_insights(df)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/{session_id}")
async def chat_with_data(session_id: str, request: ChatRequest):
    df = get_df_from_session(session_id)
    try:
        from app.agents.chat_agent import ChatAgent
        agent = ChatAgent(df)
        response = agent.process_query(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PredictRequest(BaseModel):
    target_column: str

@router.post("/predict/{session_id}")
async def run_prediction(session_id: str, request: PredictRequest):
    df = get_df_from_session(session_id)
    try:
        from app.agents.prediction_agent import PredictionAgent
        agent = PredictionAgent()
        result = agent.predict(df, request.target_column)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{session_id}/csv")
async def export_csv(session_id: str):
    df = get_df_from_session(session_id)
    from app.services.export_service import ExportService
    csv_bytes = ExportService.export_csv(df)
    
    from fastapi.responses import Response
    return Response(content=csv_bytes, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=dataset_{session_id}.csv"})

@router.get("/export/{session_id}/html")
async def export_html(session_id: str):
    df = get_df_from_session(session_id)
    from app.services.data_quality import DataQualityService
    from app.services.export_service import ExportService
    cache = active_sessions[session_id].get("metadata_cache") if session_id in active_sessions and isinstance(active_sessions[session_id], dict) else None
    quality = DataQualityService.analyze_quality(df, masks_cache=cache)
    html_bytes = ExportService.export_html(df, quality)
    
    from fastapi.responses import Response
    return Response(content=html_bytes, media_type="text/html", headers={"Content-Disposition": f"attachment; filename=report_{session_id}.html"})

@router.get("/table/{session_id}")
async def get_table_data(
    session_id: str, 
    dataset: str = "raw", 
    page: int = 1, 
    limit: int = 100, 
    search: str = "", 
    sort_col: str = "", 
    sort_order: str = "asc"
):
    session_data = active_sessions.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if isinstance(session_data, dict):
        session_data["last_accessed"] = time.time()
        
    df = get_df_from_session(session_id)
        
    try:
        # Get cached masks
        if "metadata_cache" in session_data:
            cache = session_data["metadata_cache"]
            global_dups = cache["global_dups"]
            outlier_mask = cache["outlier_mask"]
            empty_mask = cache["empty_mask"]
            missing_mask = cache["missing_mask"]
            invalid_type_mask = cache["invalid_type_mask"]
            inconsistent_cat_mask = cache["inconsistent_cat_mask"]
        else:
            from app.services.metadata_manager import MetadataManager
            cache = MetadataManager.compute_all_masks(df)
            session_data["metadata_cache"] = cache
            global_dups = cache["global_dups"]
            outlier_mask = cache["outlier_mask"]
            empty_mask = cache["empty_mask"]
            missing_mask = cache["missing_mask"]
            invalid_type_mask = cache["invalid_type_mask"]
            inconsistent_cat_mask = cache["inconsistent_cat_mask"]
            
        outlier_rows_count = int(outlier_mask.any(axis=1).sum())
        empty_cells_count = int(empty_mask.sum().sum())

        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": int(df.isna().sum().sum()),
            "empty_cells": empty_cells_count,
            "duplicates": int(global_dups.sum()),
            "outliers": outlier_rows_count
        }

        # Apply search
        mask = pd.Series(True, index=df.index)
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            
        # Apply mask to data and our flag series
        df_filtered = df[mask].copy()
        dups_filtered = global_dups[mask]
        outliers_filtered = outlier_mask[mask]
        empty_filtered = empty_mask[mask]
        missing_filtered = missing_mask[mask]
        invalid_type_filtered = invalid_type_mask[mask]
        inconsistent_cat_filtered = inconsistent_cat_mask[mask]
            
        # Apply sorting
        if sort_col and sort_col in df_filtered.columns:
            sort_idx = df_filtered[sort_col].argsort()
            if sort_order == "desc":
                sort_idx = sort_idx[::-1]
            df_filtered = df_filtered.iloc[sort_idx]
            dups_filtered = dups_filtered.iloc[sort_idx]
            outliers_filtered = outliers_filtered.iloc[sort_idx]
            empty_filtered = empty_filtered.iloc[sort_idx]
            missing_filtered = missing_filtered.iloc[sort_idx]
            invalid_type_filtered = invalid_type_filtered.iloc[sort_idx]
            inconsistent_cat_filtered = inconsistent_cat_filtered.iloc[sort_idx]
            
        total_rows = len(df_filtered)
        
        if limit > 0:
            total_pages = max(1, math.ceil(total_rows / limit))
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            df_page = df_filtered.iloc[start_idx:end_idx].copy()
            
            df_page['_is_duplicate'] = dups_filtered.iloc[start_idx:end_idx].values
            df_page['_outlier_cols'] = outliers_filtered.iloc[start_idx:end_idx].apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_empty_cols'] = empty_filtered.iloc[start_idx:end_idx].apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_missing_cols'] = missing_filtered.iloc[start_idx:end_idx].apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_invalid_type_cols'] = invalid_type_filtered.iloc[start_idx:end_idx].apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_inconsistent_category_cols'] = inconsistent_cat_filtered.iloc[start_idx:end_idx].apply(lambda row: row.index[row].tolist(), axis=1).values
        else:
            total_pages = 1
            page = 1
            df_page = df_filtered.copy()
            df_page['_is_duplicate'] = dups_filtered.values
            df_page['_outlier_cols'] = outliers_filtered.apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_empty_cols'] = empty_filtered.apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_missing_cols'] = missing_filtered.apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_invalid_type_cols'] = invalid_type_filtered.apply(lambda row: row.index[row].tolist(), axis=1).values
            df_page['_inconsistent_category_cols'] = inconsistent_cat_filtered.apply(lambda row: row.index[row].tolist(), axis=1).values
        
        # Inject the original dataframe index as a column to track rows across Raw vs Cleaned datasets
        df_page = df_page.reset_index(names=["_row_id"])
        
        # Replace NaN with None for JSON serialization
        df_page = df_page.where(pd.notnull(df_page), None)
        
        data = df_page.to_dict(orient="records")
        
        return {
            "columns": df.columns.tolist() + ["_row_id"],
            "data": data,
            "total_rows": total_rows,
            "total_pages": total_pages,
            "current_page": page,
            "stats": stats
        }
    except Exception as e:
        import traceback
        with open('error_log.txt', 'w') as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))
