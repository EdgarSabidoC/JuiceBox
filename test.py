# client.py
import asyncio
import argparse
from JuiceBoxEngine.api import JuiceBoxAPI


async def run_all_tests():
    print("\n=== TEST: GET CONFIG ===")
    print("RTB Config:", await JuiceBoxAPI.get_rtb_config())
    print("JS Config:", await JuiceBoxAPI.get_js_config())

    print("\n=== TEST: GET STATUS ===")
    print("RTB Status:", await JuiceBoxAPI.get_rtb_status())
    print("JS Status:", await JuiceBoxAPI.get_js_status())

    print("\n=== TEST: START ===")
    print("Start RTB:", await JuiceBoxAPI.start_rtb())
    print("Start JS:", await JuiceBoxAPI.start_js_container())

    print("\n=== TEST: STOP ===")
    print("Stop RTB:", await JuiceBoxAPI.stop_rtb())
    print("Stop JS:", await JuiceBoxAPI.stop_js())

    print("\n=== TEST: RESTART ===")
    print("Restart RTB:", await JuiceBoxAPI.restart_rtb_status())
    print("Restart JS:", await JuiceBoxAPI.restart_js_status())

    print("\n=== TEST: CONTAINER STATUS ===")
    print(
        "JS Container by port 3000:",
        await JuiceBoxAPI.get_js_container_status_by_port(3000),
    )
    print(
        "JS Container by name 'juice_container':",
        await JuiceBoxAPI.get_js_container_status_by_name("juice_container"),
    )

    print("\n=== TEST: STOP CONTAINER ===")
    print("Stop JS container (port 3000):", await JuiceBoxAPI.stop_js_container(3000))

    print("\n=== TEST: SET CONFIG ===")
    print("Set RTB config:", await JuiceBoxAPI.set_rtb_config({"max_users": 10}))
    print("Set JS config:", await JuiceBoxAPI.set_js_config({"ports": [3000, 3001]}))

    print("\n=== TEST: GENERATE XML ===")
    print("Generate XML:", await JuiceBoxAPI.generate_xml())


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
    print(f"{test_name}: {result}")


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
