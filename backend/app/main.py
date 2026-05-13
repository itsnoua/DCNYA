import importlib
import pkgutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules import __path__ as modules_path

app = FastAPI(
    title="AseerComplianceV2", 
    description="FastAPI + PostGIS Modular Monolith Platform",
    version="2.0.0"
)

# إعدادات CORS مطورة للسماح بجميع النطاقات (ضروري لـ Ngrok و GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def register_modules(app: FastAPI):
    """تنزيل وتسجيل الموديولات تلقائياً من مجلد modules"""
    for _, module_name, is_pkg in pkgutil.iter_modules(modules_path):
        if is_pkg:
            try:
                # 1. محاولة استيراد الموديول نفسه (في حال تم التصدير في __init__.py)
                module = importlib.import_module(f"app.modules.{module_name}")
                router = getattr(module, "router", None)
                
                # 2. إذا لم يوجد، نحاول استيراد ملف router.py مباشرة
                if not router:
                    router_module = importlib.import_module(f"app.modules.{module_name}.router")
                    router = getattr(router_module, "router", None)
                
                if router:
                    app.include_router(
                        router,
                        prefix=f"/api/{module_name}",
                        tags=[module_name.capitalize()]
                    )
                    print(f"Module '{module_name}' registered at /api/{module_name}")
            except Exception as e:
                print(f"Error registering module '{module_name}': {e}")

# تسجيل الموديولات تلقائياً
register_modules(app)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Aseer Compliance Modular Monolith API",
        "status": "Running"
    }
