import nox

PYPROJECT = nox.project.load_toml('pyproject.toml')

PYTHONS = [
    # Reads versions from Trove classifiers
    *nox.project.python_versions(PYPROJECT),
]

# Prefer uv to create virtual environments, fall back to virtualenv.
# Overriden by $NOX_DEFAULT_VENV_BACKEND=... or nox --default-venv-backend ...
# https://nox.thea.codes/en/stable/usage.html#changing-the-sessions-default-backend
nox.options.default_venv_backend = 'uv|virtualenv'

@nox.session(python=PYTHONS, tags=["test"])
def tests(session):
    session.install('.[testing]')
    session.run('coverage', 'run', '-m', 'pytest')
