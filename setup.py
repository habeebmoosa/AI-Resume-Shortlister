from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='ai_resume_shortlister',
    version='0.1',
    packages=find_packages(),
    install_requires=requirements,
)
