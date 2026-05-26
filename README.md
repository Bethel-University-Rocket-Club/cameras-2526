# Bethel University Camera Code 25/26

For part A in the ["Secret Message Challenge from the Midwest Rocketry Competition 2025/2026](https://dept.aem.umn.edu/mnsgc/Space_Grant_Midwest_Rocketry_Competition_2025_2026/Midwest_Rocketry_Competition_Handbook_2025-2026_v7.pdf#page=4). Including lights indicating status of the roll control system as per part B.

Controls the gathering and transmission of wireless video. Hosts an Access Point to receive data to control LED's.

## Architecture

This system was designed to manage indicator lights with information from an external system, and to collect then transmit video via 4G LTE.

### Dataflow

There are two distinct dataflow's in this system.

#### Indicator Lights

```mermaid
graph LR
    external[roll control] --> wireless[wireless] --> process[process information] --> led[drive LEDs on/off]
```

#### Camera Video

```mermaid
graph LR
    camera[Pi Camera Module V2] --> processing[FFMPEG] --> save[Save as .mp4] --> LTE[make video available via LTE]
```

### Control Flow

There are two distinct control flow's in this system.

#### Indicator Lights

```mermaid
graph LR
    power[Power on] --> AP[start Access Point] --> listen[listen for wireless commands] --> led[drive LEDs on/off]
```

#### Camera Video

```mermaid
graph LR
    power[Power on] --> LTE[start LTE] --> user_cmd[wait for wireless user command] --> video[take video for 120 seconds] --> convet[convert video with FFMPEG to .mp4]
```

## Design Decisions

Some insight to some decisions that were made when designing this system.

### Startup Services

To decouple user interaction as much as possible from the system several systems start once the system receives power.

#### flight

Receives wireless packets to drive LED's in an endless loop.

#### simcom-connect

Starts the LTE telemetry transmission capabilities.

### User Controls

Due to day of sensor difficulties, wireless manual user overrides were added to complete the challenge.

#### Camera Start

The user must manually start ```cam_atmpt.py``` for the camera to begin its recording and converting process.

## Limitations

The end design of this system has several limitations that need to be considered when using.

### Wireless Reliant

As the camera system is only startable by an external user, it is currently a requirement that the user is either connected via LTE, or via the system's wireless Access Point.

### Location Dependent

Since the system uses 4G LTE, it is entire locationally dependent on whether the primary telemetry system works. It is also outside of the user's control whether the LTE in the area works consistently.

## Retrospective

Due to physical wiring constraings, a last minute reorganization of the system had to occur. This rapid change showed how design decisons impacted how the system can be adapted.

### Reproducibility

Due to the system being hosted on a Pi Zero 2W as a full Operating System, reproducing its exact state eventually proved to be near impossible without a full disk image of the 32GB sd-card.

Keeping better documentation of every step taken to setup the OS, or using an OS like NixOS would allow faster saving of the system without needing to copy the entire disk. 

### Modularity

Prior to the reorganization of the system, ```flight.py``` contained all the code for running the camera system and the LED's. 

This was a workable decision as the camera system code was isolated enough it could be removed and put in a separate ```.py``` file for manual running, however it should have been a callable function in its own file from the beginning.

The wireless roll control LED part of the system should have also been in its own file as a function, ```flight.py``` should have been the facilitator of code, rather than the container for it.

## Lite User Guide

The file structure of this repository reflects where the files are expected to go. Raspberry Pi OS Lite was the base OS used. Configured to act as an SSH server and as a wireless AP.

### Commands

The following is some useful commands for using the system.

#### Systemctl

These commands are used to check and set the startup/running status of ```flight``` or ```simcom-connect```.

- ```sudo systemctl status [system]```
    - displays the current running status of the specified system
- ```sudo systemctl stop [system]```
    - stops running the specified system
- ```sudo systemctl start [system]```
    - starts running the specified system if it is not already running
- ```sudo systemctl enable [system]```
    - enables running the specified system on power on
- ```sudo systemctl disable [system]```
    - disables running the specified system on power off

#### NOHUP

The command used on launch day to start the camera system to allow it to continue running even if connection was launched was ```sudo nohup python3 cam_atmpy.py &```