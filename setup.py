from setuptools import setup

setup(
    name='msk',
    version='0.1.2',  # Also update in msu/__init__.py
    packages=['msk'],
    install_requires=['GitPython', 'typing', 'msm', 'pygithub', 'future'],
    url='https://github.com/MycroftAI/mycroft-skills-kit',
    license='MIT',
    author='Mycroft AI',
    author_email='support@mycroft.ai',
    maintainer='Matthew Scholefield',
    maintainer_email='matthew331199@gmail.com',
    description='Mycroft Skills Kit',
    entry_points={
        'console_scripts': {
            'msk=msk.__main__:main'
        }
    }
)
