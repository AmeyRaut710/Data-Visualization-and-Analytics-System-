from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.dashboard_engine import PowerBIDashboardEngine
from app.api.routes import get_df_from_session, active_sessions

router = APIRouter()

class DashboardFilterRequest(BaseModel):
    filters: Dict[str, Any]
    sheet: Optional[str] = None

@router.post("/{session_id}/generate")
async def generate_dashboard(session_id: str, sheet: str = None):
    try:
        df = get_df_from_session(session_id, sheet=sheet)
        
        session_data = active_sessions.get(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
            
        target_sheet = sheet if sheet and "sheets" in session_data and sheet in session_data["sheets"] else session_data.get("default_sheet")
        sheet_data = session_data["sheets"][target_sheet] if "sheets" in session_data and target_sheet else session_data
        
        dataset_name = target_sheet if target_sheet else "Dataset"
        
        config = PowerBIDashboardEngine.generate(df, dataset_name)
        sheet_data["dashboard_config"] = config
        
        return config
    except Exception as e:
        import traceback
        with open("dashboard_error.txt", "w") as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/filter")
async def filter_dashboard(session_id: str, request: DashboardFilterRequest):
    try:
        df = get_df_from_session(session_id, sheet=request.sheet)
        
        session_data = active_sessions.get(session_id)
        target_sheet = request.sheet if request.sheet and "sheets" in session_data and request.sheet in session_data["sheets"] else session_data.get("default_sheet")
        sheet_data = session_data["sheets"][target_sheet] if "sheets" in session_data and target_sheet else session_data
        
        if "dashboard_config" not in sheet_data:
            raise HTTPException(status_code=400, detail="Dashboard not generated yet.")
            
        base_config = sheet_data["dashboard_config"]
        
        filtered_config = PowerBIDashboardEngine.apply_filters(df, request.filters, base_config)
        
        return filtered_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
