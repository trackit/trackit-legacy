![Image](https://s3-us-west-2.amazonaws.com/trackit-public-artifacts/github-page/logo.png)

## Don't want to self-host TrackIt?

We run our own version, check it out at [TrackIt.IO](https://trackit.io/)


## Installation

#### #0 Be sure all requirements below are met


#### #1 Clone TrackIt
```sh
$> git clone https://github.com/trackit/trackit.git && cd trackit
```

#### #2 Start TrackIt and Let's Go!
```sh
$> ./run.sh
```
_If you are on a headless machine, you should set the **TRACKIT_HOST** environment variable to change the IP where TrackIt will listen._

See the [Setup Guide](https://www.trackit.io/#/app/setupguide) to know how to add your AWS key to TrackIt.

Want to shutdown TrackIt?
```sh
$> docker-compose down
```


## Default credential

```
username: admin
password: admin
```


## Software Requirement

#### Docker Engine
How to install [Docker Engine](https://docs.docker.com/engine/installation/)

#### Docker Compose
How to install [Docker Compose](https://docs.docker.com/compose/install/)


## Hardware Requirement
Currently, we recommend having a minimal of 2 cores and 2GB of RAM to run TrackIt.
The disk space entirely depends on your billing file's size and your seniority on AWS. You should start with 32GB free.
We have found that an account spending $300,000 a month for 24 months in AWS takes around 50GB more.

## Screenshots

Home page with different cost and usage charts

![Image](https://s3-us-west-2.amazonaws.com/trackit-public-artifacts/github-page/home.png)


List of your resources

![Image](https://s3-us-west-2.amazonaws.com/trackit-public-artifacts/github-page/VM.png)


Cost forecast and suggestions

![Image](https://s3-us-west-2.amazonaws.com/trackit-public-artifacts/github-page/forecast.png)


## Support and Contact

See the [contact page](https://www.trackit.io/landing/#contact).
