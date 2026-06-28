from setuptools import setup, Extension

module_name = "virtual_console"

module = Extension(module_name, sources=["virtual_console.cpp"])

setup(name=module_name,
	  version="0.0.1",
	  description="Virtual console beta",
	  ext_modules=[module]
)