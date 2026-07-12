"""
Entry point: Run the Seto research dashboard with sub-controller.
 
Usage:
  python run_seto_dashboard.py         # Start dashboard on :8891
  python run_seto_dashboard.py --port 8891 --host 0.0.0.0
"""

import argparse
import asyncio
import sys

sys.path.insert(0, ".")


def main():
    parser = argparse.ArgumentParser(description="Seto Research Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8891, help="Bind port")
    args = parser.parse_args()

    # Bootstrap the sub-controller and dashboard
    from app.apithon_mcp.sub_controller import get_sub_controller
    from app.apithon_mcp.seto_dashboard import run_dashboard

    # Initialize sub-controller (singleton)
    sc = get_sub_controller()
    print(f"⚡ Sub-controller online: {sc}")
    
    # Check APITHON availability
    from app.apithon_mcp.bridge import check_apithon
    status = check_apithon()
    print(f"🔌 APITHON protocols: { {k: '✓' if v else '✗' for k, v in status.items()} }")

    run_dashboard(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
