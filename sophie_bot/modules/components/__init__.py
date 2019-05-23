from sophie_bot import NO_LOAD_COMPONENTS, logger


def list_all_components():
    from os.path import dirname, basename, isfile
    import glob

    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_components = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]
    return all_components


ALL_COMPONENTS = sorted(list_all_components())

for component in ALL_COMPONENTS:
    if component in NO_LOAD_COMPONENTS:
        ALL_COMPONENTS.remove(component)
logger.info("Components to load: %s", str(ALL_COMPONENTS))
__all__ = ALL_COMPONENTS + ["ALL_COMPONENTS"]
