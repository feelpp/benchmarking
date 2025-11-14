from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("feelpp.benchmarking")
except PackageNotFoundError:
    __version__ = "0.0.0"
