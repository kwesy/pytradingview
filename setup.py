from setuptools import setup, find_packages


setup(
    name="pytradingview",
    version="0.1.1",
    packages=find_packages(),
    install_requires=["websocket-client>=1.5.1"],
    author="Onesimus Graves-Sampson",
    description="A Python client for TradingView WebSocket API. It's a lightweight library capable of providing real-time data on stocks, cryptocurrencies, indices etc.",
    # license="MIT",
    # keywords=["tradingview", "trading", "forex", "stocks", "crypto"],
    url="https://github.com/kwesy/pytradingview.git",
    entry_points={
        'console_scripts': [
            'pytradingview = pytradingview.__main__:main'
        ]
    },
)
