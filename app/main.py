from fastapi import FastAPI

from app.routes import health_router, invoices_router,items_router

app = FastAPI(title="Backend Exercise API", version="1.0.0")

# Register routers
app.include_router(health_router)
app.include_router(items_router)
app.include_router(invoices_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
