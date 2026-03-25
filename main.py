import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from litellm import completion
from docx import Document
import uvicorn

app = FastAPI()

# 1. FIX CORS (The Bouncer)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. SYNCED DATA MODEL (Matches your HTML payload exactly)
class ProjectDetails(BaseModel):
    project_name: str = "N/A"
    project_desc: str = "N/A"
    data_subjects: str = "N/A"
    data_collected: str = "N/A"
    retention_period: str = "N/A"
    third_parties: str = "N/A"
    initial_risk: str = "Medium"
    license_key: str = "FREE"
    geo_scope: str = "N/A"
    lawful_basis: str = "N/A"
    collection_source: str = "N/A"
    purpose_assessment: str = "N/A"
    transparency_measures: str = "N/A"
    data_minimization: str = "N/A"
    data_quality: str = "N/A"
    security_measures: str = "N/A"
    intl_transfers: str = "N/A"
    retention_policy: str = "N/A"
    individual_rights: str = "N/A"

class FinalReportRequest(ProjectDetails):
    identified_risks: str = "N/A"

@app.get("/")
def home():
    return {"message": "DPIA API is Online"}

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    # This prompt tells the AI to use all your new audit criteria
    prompt = f"""
    Act as a Senior Privacy Counsel. Conduct a professional DPIA risk assessment.
    
    AUDIT CRITERIA:
    - PROJECT: {data.project_name}
    - GEOGRAPHIC SCOPE: {data.geo_scope}
    - PURPOSE: {data.purpose_assessment}
    - LAWFUL BASIS: {data.lawful_basis}
    - SOURCE OF DATA: {data.collection_source}
    - DATA MINIMIZATION: {data.data_minimization}
    - SECURITY MEASURES: {data.security_measures}
    - DATA QUALITY: {data.data_quality}
    - INDIVIDUAL RIGHTS: {data.individual_rights}
    - RETENTION: {data.retention_period}
    
    Please provide a structured legal analysis of potential privacy risks and technical mitigations.
    """
    try:
        # Using Gemini 2.5 Flash
        response = completion(model="gemini/gemini-2.5-flash", messages=[{"role": "user", "content": prompt}])
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        print(f"CRASH ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-report")
async def generate_final_report(data: FinalReportRequest):
    try:
        doc = Document()
        doc.add_heading('Data Protection Impact Assessment (DPIA)', 0)
        
        # Adding Project Summary
        doc.add_heading('1. Project Overview', level=1)
        doc.add_paragraph(f"Project Name: {data.project_name}")
        doc.add_paragraph(f"Geographic Scope: {data.geo_scope}")
        doc.add_paragraph(f"Lawful Basis: {data.lawful_basis}")
        
        doc.add_heading('2. Risk Assessment Findings', level=1)
        doc.add_paragraph(data.identified_risks)
        
        file_path = f"/tmp/DPIA_Report.docx"
        doc.save(file_path)
        return FileResponse(path=file_path, filename=f"{data.project_name}_DPIA.docx")
    except Exception as e:
        return {"status": "error", "message": str(e)}
