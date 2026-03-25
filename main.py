# --- UPDATE THIS CLASS AT THE TOP ---
class ProjectDetails(BaseModel):
    license_key: str = "FREE"
    project_name: str
    project_desc: str
    geo_scope: str
    data_subjects: str
    data_collected: str
    collection_source: str
    purpose_assessment: str
    transparency_measures: str
    data_minimization: str
    data_quality: str
    security_measures: str
    intl_transfers: str
    retention_period: str # Matches HTML id p_retention
    individual_rights: str
    initial_risk: str

# --- UPDATE THE ANALYZE FUNCTION ---
@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"""
    Act as a Senior Privacy Counsel. Conduct a DPIA risk assessment for:
    Project: {data.project_name} in {data.geo_scope}.
    Basis: {data.lawful_basis} (N/A if not provided)
    Description: {data.project_desc}
    Data: {data.data_collected} (Source: {data.collection_source})
    Security: {data.security_measures}
    Retention: {data.retention_period}
    
    Please provide a detailed risk analysis and mitigations based on these audit criteria.
    """
    try:
        response = completion(model="gemini/gemini-2.5-flash", messages=[{"role": "user", "content": prompt}])
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}
