def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", default=False,
                     help="Run live tests that hit Urban Dictionary")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return
    skip = __import__("pytest").mark.skip(reason="use --run-live to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
