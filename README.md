## furday

 [![Python versions](https://img.shields.io/pypi/pyversions/birdysis.svg)](https://pypi.python.org/pypi/birdysis/) [![PyPI](https://img.shields.io/pypi/v/birdysis.svg)](https://pypi.python.org/pypi/birdysis/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-black)](https://github.com/PyCQA/flake8)
 
furday manages + fetches daily character posts from ![@daily_furry](https://twitter.com/daily_furry?lang=en)

## Purpose
<sub>a daily furry!</sub>
<sub>thank you @TommoTheCabbit</sub>

<img align="right" height="140" width="140" src=https://pbs.twimg.com/profile_images/1377740950584328192/YOJr-Xph_400x400.png>


## Installation

Requires discord.py + PSQL credentials for data handling and bot storage.
For quick hosting + PSQL integration, I recommend using ![Heroku](https://www.heroku.com/) and using `psycopg2` for API requests.
Alternatively, local hosting on pm2 (launch as a service) or deploying to Docker are other methods of hosting, but require manual installing of PSQL (dependent on machine).

## Goals

- Implement multiple server activations.
- Add more functions to reset tables/databases (requires Admin access, exclusive to guild/server).
- Add more utility functions + data viewing functions.


## Contributing
Pull requests are always welcome! Any major changes you wish to implement should first be initiated with an issue + pull request (updating tests as necessary).

## Major Technologies
- [psycog2](https://selenium-python.readthedocs.io/) (3.141.0)
- [discord.py](https://docs.tweepy.org/en/latest/) (3.10.0)
- [pm2](https://pm2.keymetrics.io/docs/usage/quick-start/) (4.5.6)
- [docker](https://docker.com) (20.10.7)
- [tweepy](https://pypi.org/project/tweepy/) (3.10.0)

## License
[MIT](https://choosealicense.com/licenses/mit/)

