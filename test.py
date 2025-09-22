# client.py
import asyncio
import argparse
from JuiceBoxEngine.api import JuiceBoxAPI


def print_response(res):
    """Helper para imprimir un ManagerResult o Response de forma legible."""
    if res is None:
        print("Response is None")
        return
    # Campos comunes: status, message, error, data
    success = getattr(res, "status", None)
    message = getattr(res, "message", None)
    error = getattr(res, "error", None)
    data = getattr(res, "data", None)

    print(f"Success: {success}")
    print(f"Message: {message}")
    if error:
        print(f"Error: {error}")
    if data:
        print(f"Data: {data}")
    print("-" * 40)


async def run_all_tests():
    print("\n=== TEST: START ===")
    print_response(await JuiceBoxAPI.start_rtb())
    print_response(await JuiceBoxAPI.start_js_container())

    print("\n=== TEST: GET STATUS ===")
    print_response(await JuiceBoxAPI.get_rtb_status())
    print_response(await JuiceBoxAPI.get_js_status())

    print("\n=== TEST: GET CONFIG ===")
    print_response(await JuiceBoxAPI.get_rtb_config())
    print_response(await JuiceBoxAPI.get_js_config())

    print("\n=== TEST: STOP ===")
    print_response(await JuiceBoxAPI.stop_rtb())
    print_response(await JuiceBoxAPI.stop_js())

    print("\n=== TEST: RESTART ===")
    print_response(await JuiceBoxAPI.restart_rtb_status())
    print_response(await JuiceBoxAPI.restart_js_status())

    print("\n=== TEST: CONTAINER STATUS ===")
    print_response(await JuiceBoxAPI.get_js_container_status_by_port(3000))

    print("\n=== TEST: STOP CONTAINER ===")
    print_response(await JuiceBoxAPI.stop_js_container(3000))

    print("\n=== TEST: SET CONFIG ===")
    print_response(
        await JuiceBoxAPI.set_rtb_config({"webapp_port": 8889, "lifespan": 1})
    )
    print_response(
        await JuiceBoxAPI.set_js_config(
            {"ctf_key": "test1", "ports_range": [3000, 3001]}
        )
    )

    print("\n=== TEST: GET CONFIG AFTER SET ===")
    print_response(await JuiceBoxAPI.get_rtb_config())
    print_response(await JuiceBoxAPI.get_js_config())

    print("\n=== TEST: GENERATE XML ===")
    print_response(await JuiceBoxAPI.generate_xml())


async def run_one_test(test_name: str):
    mapping = {
        "rtb_config": JuiceBoxAPI.get_rtb_config,
        "js_config": JuiceBoxAPI.get_js_config,
        "rtb_status": JuiceBoxAPI.get_rtb_status,
        "js_status": JuiceBoxAPI.get_js_status,
        "start_rtb": JuiceBoxAPI.start_rtb,
        "start_js": JuiceBoxAPI.start_js_container,
        "stop_rtb": JuiceBoxAPI.stop_rtb,
        "stop_js": JuiceBoxAPI.stop_js,
        "restart_rtb": JuiceBoxAPI.restart_rtb_status,
        "restart_js": JuiceBoxAPI.restart_js_status,
        "generate_xml": JuiceBoxAPI.generate_xml,
    }

    if test_name not in mapping:
        print(f"Unknown test '{test_name}'")
        return

    result = await mapping[test_name]()
    print_response(result)


def main():
    parser = argparse.ArgumentParser(description="JuiceBox API test client")
    parser.add_argument(
        "--test", type=str, help="Run one specific test (e.g., 'rtb_config')"
    )
    args = parser.parse_args()

    if args.test:
        asyncio.run(run_one_test(args.test))
    else:
        asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
