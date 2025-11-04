"""
Script to verify all routes are registered
Run this to check if search-ubo endpoint is available
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi import FastAPI
    from api.endpoints import router
    
    app = FastAPI()
    app.include_router(router, prefix="/api/v1", tags=["ubo-trace"])
    
    # Get all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method != 'HEAD':  # Skip HEAD methods
                    routes.append(f"{method} {route.path}")
    
    print("\n=== Registered Routes ===")
    for route in sorted(routes):
        print(route)
    
    # Check specifically for search-ubo
    search_ubo_found = any('/search-ubo' in r for r in routes)
    print(f"\n✓ search-ubo endpoint found: {search_ubo_found}")
    
    if not search_ubo_found:
        print("\n⚠ WARNING: /search-ubo endpoint not found in registered routes!")
        print("This might indicate an import error when loading endpoints.py")
    
except Exception as e:
    print(f"\n✗ Error loading routes: {e}")
    import traceback
    traceback.print_exc()

