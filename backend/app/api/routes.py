from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_ingestion import DataIngestionService
from app.models.schemas import DatasetOverviewResponse, DataQualityResponse
from app.core.state import active_sessions
import uuid
import gc
import math
import polars as pl
import time

router = APIRouter()

def sweep_expired_sessions():
    now = time.time()
    expired = [sid for sid, data in active_sessions.items() if isinstance(data, dict) and now - data.get("last_accessed", now) > 3600]
    for sid in expired:
        del active_sessions[sid]
    if expired:
        gc.collect()

def get_df_from_session(session_id: str, dataset: str = "cleaned") -> pl.DataFrame:
    session_data = active_sessions.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if isinstance(session_data, dict):
        session_data["last_accessed"] = time.time()
        if dataset == "raw" and "raw" in session_data:
            return session_data["raw"]
            
        if "history" in session_data and "history_pointer" in session_data:
            ptr = session_data["history_pointer"]
            if 0 <= ptr < len(session_data["history"]):
                return session_data["history"][ptr]
        if "history" in session_data and len(session_data["history"]) > 0:
            return session_data["history"][-1]
        elif "raw" in session_data:
            return session_data.get("cleaned") if session_data.get("cleaned") is not None else session_data.get("raw")
        return session_data["raw"]

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
            "history_pointer": 0,
            "raw": df, 
            "cleaned": df, 
            "last_accessed": time.time()
        }
        
        from app.services.metadata_manager import MetadataManager
        cache, typed_df = MetadataManager.compute_all_masks(df)
        active_sessions[session_id]["metadata_cache"] = cache
        active_sessions[session_id]["raw_metadata_cache"] = cache
        
        active_sessions[session_id]["history"][0] = typed_df
        active_sessions[session_id]["raw"] = typed_df
        active_sessions[session_id]["cleaned"] = typed_df
        active_sessions[session_id]["ignored_issues"] = {}
        df = typed_df
        
        overview = DataIngestionService.get_overview(df, file.filename, len(content))
        
        return {
            "session_id": session_id,
            "overview": overview
        }
    except Exception as e:
        import traceback
        with open('upload_error.txt', 'w') as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in active_sessions:
        del active_sessions[session_id]
        gc.collect()
        return {"message": "Session and all associated data permanently deleted from memory."}
    return {"message": "Session not found."}

@router.get("/quality/{session_id}")
async def get_data_quality(session_id: str):
    df = get_df_from_session(session_id)
    try:
        from app.services.data_quality import DataQualityService
        
        cache = active_sessions[session_id].get("metadata_cache") if session_id in active_sessions and isinstance(active_sessions[session_id], dict) else None
        quality_report = DataQualityService.analyze_quality(df, masks_cache=cache)
        
        quality_report["ai_health_report"] = None
        
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

class ChatRequest(BaseModel):
    message: str

@router.post("/clean/{session_id}/preview")
async def preview_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        from app.services.data_cleaning import DataCleaningService
        cleaned_df = DataCleaningService.apply_targeted_cleaning(df, request.issue, request.columns, request.method, request.custom_value)
        
        values_changed = 0
        if df.height != cleaned_df.height:
            rows_removed = df.height - cleaned_df.height
            try:
                dropped = df.join(cleaned_df, on=df.columns, how="anti").head(5)
                original_preview = dropped.to_dicts()
                cleaned_preview = []
            except:
                original_preview = df.head(5).to_dicts()
                cleaned_preview = cleaned_df.head(5).to_dicts()
        else:
            rows_removed = 0
            diff_mask = pl.Series([False] * df.height)
            for col in df.columns:
                s1 = df.get_column(col)
                s2 = cleaned_df.get_column(col)
                null_diff = s1.is_null() != s2.is_null()
                try:
                    val_diff = (s1.is_not_null() & s2.is_not_null()) & (s1 != s2)
                except:
                    val_diff = (s1.is_not_null() & s2.is_not_null()) & (s1.cast(pl.Utf8) != s2.cast(pl.Utf8))
                col_diff = null_diff | val_diff
                diff_mask = diff_mask | col_diff
                
            values_changed = diff_mask.sum()
            changed_orig = df.filter(diff_mask).head(5)
            changed_new = cleaned_df.filter(diff_mask).head(5)
            
            original_preview = changed_orig.to_dicts()
            cleaned_preview = changed_new.to_dicts()
            
            if not original_preview:
                original_preview = df.head(5).to_dicts()
                cleaned_preview = cleaned_df.head(5).to_dicts()
        
        # Replace NaN with None in dicts
        def clean_dict(d_list):
            import math
            for d in d_list:
                for k, v in d.items():
                    if isinstance(v, float) and math.isnan(v):
                        d[k] = None
            return d_list

        return {
            "original_preview": clean_dict(original_preview),
            "cleaned_preview": clean_dict(cleaned_preview),
            "metrics": {
                "rows_affected": rows_removed or values_changed,
                "values_changed": values_changed,
                "rows_removed": rows_removed,
                "estimated_quality_improvement": "+2.5%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clean/{session_id}/apply")
async def apply_cleaning(session_id: str, request: TargetedCleanRequest):
    import asyncio
    await asyncio.sleep(2)
    df = get_df_from_session(session_id)
    try:
        from app.services.data_cleaning import DataCleaningService
        cache = active_sessions[session_id].get("metadata_cache") if session_id in active_sessions and isinstance(active_sessions[session_id], dict) else None
        cleaned_df = DataCleaningService.apply_targeted_cleaning(df, request.issue, request.columns, request.method, request.custom_value, cache)
        
        if session_id in active_sessions and isinstance(active_sessions[session_id], dict):
            session = active_sessions[session_id]
            ptr = session.get("history_pointer", 0)
            
            # Branch history if we are not at the end
            session["history"] = session["history"][:ptr + 1]
            session["history_logs"] = session["history_logs"][:ptr + 1]
            
            session["history"].append(cleaned_df)
            
            cols_str = "all columns" if not request.columns or request.columns == ['all'] else ", ".join(str(c) for c in request.columns)
            action_desc = f"{request.method} applied to {cols_str} for {request.issue}"
            session["history_logs"].append(action_desc)
            session["history_pointer"] = ptr + 1
            session["cleaned"] = cleaned_df
            
            if request.method == 'Ignore':
                if "ignored_issues" not in session:
                    session["ignored_issues"] = {}
                if request.issue not in session["ignored_issues"]:
                    session["ignored_issues"][request.issue] = []
                for col in request.columns:
                    if col not in session["ignored_issues"][request.issue]:
                        session["ignored_issues"][request.issue].append(col)
            
            ignored = session.get("ignored_issues", {})
            
            from app.services.metadata_manager import MetadataManager
            cache = active_sessions[session_id].get("metadata_cache")
            if cache:
                if df.height != cleaned_df.height:
                    cache, typed_df = MetadataManager.compute_all_masks(cleaned_df, ignored)
                else:
                    cache, typed_df = MetadataManager.update_masks(cleaned_df, cache, request.issue, request.columns, ignored)
            else:
                cache, typed_df = MetadataManager.compute_all_masks(cleaned_df, ignored)
                
            active_sessions[session_id]["metadata_cache"] = cache
            cleaned_df = typed_df
            gc.collect()
            
        rows_affected = df.height - cleaned_df.height
        
        from app.services.data_quality import DataQualityService
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
        
    ptr = session_data.get("history_pointer", 0)
    if ptr > 0:
        session_data["history_pointer"] = ptr - 1
        from app.services.metadata_manager import MetadataManager
        df = session_data["history"][ptr - 1]
        session_data["cleaned"] = df
        cache, typed_df = MetadataManager.compute_all_masks(df, session_data.get("ignored_issues", {}))
        session_data["metadata_cache"] = cache
        session_data["cleaned"] = typed_df
        gc.collect()
        return {"message": "Undo successful"}
    else:
        raise HTTPException(status_code=400, detail="Nothing to undo")

@router.post("/clean/{session_id}/redo")
async def redo_cleaning(session_id: str):
    session_data = active_sessions.get(session_id)
    if not session_data or not isinstance(session_data, dict):
        raise HTTPException(status_code=404, detail="Session not found")
        
    ptr = session_data.get("history_pointer", 0)
    history = session_data.get("history", [])
    if ptr < len(history) - 1:
        session_data["history_pointer"] = ptr + 1
        from app.services.metadata_manager import MetadataManager
        df = history[ptr + 1]
        session_data["cleaned"] = df
        cache, typed_df = MetadataManager.compute_all_masks(df, session_data.get("ignored_issues", {}))
        session_data["metadata_cache"] = cache
        session_data["cleaned"] = typed_df
        gc.collect()
        return {"message": "Redo successful"}
    else:
        raise HTTPException(status_code=400, detail="Nothing to redo")

@router.get("/clean/{session_id}/history")
async def get_cleaning_history(session_id: str):
    session_data = active_sessions.get(session_id)
    if not session_data or not isinstance(session_data, dict):
        raise HTTPException(status_code=404, detail="Session not found")
        
    logs = session_data.get("history_logs", [])
    ptr = session_data.get("history_pointer", 0)
    return {"history": logs, "pointer": ptr}

@router.post("/clean/{session_id}/recommend")
async def recommend_cleaning(session_id: str, request: TargetedCleanRequest):
    df = get_df_from_session(session_id)
    try:
        from app.agents.cleaning_agent import CleaningAgent
        agent = CleaningAgent()
        
        stats = {}
        for col in request.columns:
            if col in df.columns:
                s = df.get_column(col)
                stats[col] = {
                    "type": str(s.dtype),
                    "missing": s.null_count(),
                    "unique": s.n_unique()
                }
        
        rec = agent.recommend(request.issue, ", ".join(request.columns), stats)
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/{session_id}")
async def get_visualizations(session_id: str):
    df = get_df_from_session(session_id)
    try:
        from app.agents.visualization_agent import VisualizationAgent
        agent = VisualizationAgent()
        # Requires pandas DataFrame fallback temporarily for visualizations
        charts_config = agent.generate_visualizations(df.to_pandas())
        return {"visualizations": charts_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{session_id}/csv")
async def export_csv(session_id: str):
    df = get_df_from_session(session_id)
    from fastapi.responses import Response
    csv_bytes = df.write_csv()
    return Response(content=csv_bytes, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=dataset_{session_id}.csv"})

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

    df = get_df_from_session(session_id, dataset)
    
    try:
        from app.services.metadata_manager import MetadataManager
        if dataset == "raw":
            cache = session_data.get("raw_metadata_cache")
            if not cache:
                cache, typed_df = MetadataManager.compute_all_masks(df)
                session_data["raw_metadata_cache"] = cache
                session_data["raw"] = typed_df
                df = typed_df
        else:
            cache = session_data.get("metadata_cache")
            if not cache:
                cache, typed_df = MetadataManager.compute_all_masks(df, session_data.get("ignored_issues", {}))
                session_data["metadata_cache"] = cache
                session_data["cleaned"] = typed_df
                df = typed_df
    except Exception as e:
        cache = {}
    
    # Calculate stats for the response
    global_dups_idx = cache.get("global_dups_idx", [])
    outlier_rows_count = sum(len(idx) for idx in cache.get("outlier_indices", {}).values())
    empty_cells_count = sum(len(idx) for idx in cache.get("empty_indices", {}).values())
    missing_cells_count = sum(len(idx) for idx in cache.get("missing_indices", {}).values())

    outlier_metadata = {}
    for col, col_stats in cache.get("stats", {}).items():
        if isinstance(col_stats, dict) and 'outlier_method' in col_stats:
            outlier_metadata[col] = {
                "method": col_stats["outlier_method"],
                "lower_bound": col_stats["lower_bound"],
                "upper_bound": col_stats["upper_bound"]
            }

    from app.services.data_quality import DataQualityService
    try:
        quality_report = DataQualityService.analyze_quality(df, masks_cache=cache)
        quality_score = quality_report.get("scores", {}).get("overall_cleanliness", 0)
    except:
        quality_score = 0

    stats = {
        "total_rows": df.height,
        "total_columns": df.width,
        "missing_values": missing_cells_count,
        "empty_cells": empty_cells_count,
        "duplicates": len(global_dups_idx),
        "outliers": outlier_rows_count,
        "outlier_metadata": outlier_metadata,
        "quality_score": quality_score
    }

    df_filtered = df.with_row_index("_row_id")
    
    if search:
        search = search.lower()
        exprs = [pl.col(c).cast(pl.Utf8).str.to_lowercase().str.contains(search) for c in df.columns if df.schema[c] in [pl.Utf8, pl.Categorical]]
        if exprs:
            df_filtered = df_filtered.filter(pl.any_horizontal(exprs))
            
    if sort_col and sort_col in df_filtered.columns:
        df_filtered = df_filtered.sort(sort_col, descending=(sort_order == "desc"))
        
    total_rows = df_filtered.height
    
    if limit > 0:
        total_pages = max(1, math.ceil(total_rows / limit))
        df_page = df_filtered.slice((page - 1) * limit, limit)
    else:
        total_pages = 1
        df_page = df_filtered
        
    # Convert to dicts for JSON
    page_dicts = df_page.to_dicts()
    
    # Inject metadata efficiently for only the rows in the page
    global_dups_set = set(global_dups_idx)
    outlier_sets = {col: set(idx_list) for col, idx_list in cache.get("outlier_indices", {}).items()}
    empty_sets = {col: set(idx_list) for col, idx_list in cache.get("empty_indices", {}).items()}
    missing_sets = {col: set(idx_list) for col, idx_list in cache.get("missing_indices", {}).items()}
    invalid_type_sets = {col: set(idx_list) for col, idx_list in cache.get("invalid_type_indices", {}).items()}
    inconsistent_cat_sets = {col: set(idx_list) for col, idx_list in cache.get("inconsistent_cat_indices", {}).items()}
    
    for row in page_dicts:
        r_idx = row["_row_id"]
        row["_is_duplicate"] = r_idx in global_dups_set
        
        row["_outlier_cols"] = [col for col, idx_set in outlier_sets.items() if r_idx in idx_set]
        row["_empty_cols"] = [col for col, idx_set in empty_sets.items() if r_idx in idx_set]
        row["_missing_cols"] = [col for col, idx_set in missing_sets.items() if r_idx in idx_set]
        row["_invalid_type_cols"] = [col for col, idx_set in invalid_type_sets.items() if r_idx in idx_set]
        row["_inconsistent_category_cols"] = [col for col, idx_set in inconsistent_cat_sets.items() if r_idx in idx_set]
        
        for k, v in row.items():
            if v != v: # Check for NaN since Polars keeps NaN for floats
                row[k] = None

    return {
        "columns": df.columns + ["_row_id"],
        "data": page_dicts,
        "total_rows": total_rows,
        "total_pages": total_pages,
        "current_page": page,
        "stats": stats
    }

