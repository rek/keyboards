/*
Copyright 2012 Jun Wako <wakojun@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#pragma once

#define MASTER_LEFT
//#define MASTER_RIGHT

//#define EE_HANDS

/* PMW33XX Settings */
#define PMW33XX_CS_PIN           D9
#define POINTING_DEVICE_LEFT
// #define MOUSE_SHARED_EP = yes
// #define SPLIT_POINTING_ENABLE
// #define ROTATIONAL_TRANSFORM_ANGLE  -25

// This sets the polling to 1ms, or a 1000 times per second, which the sensor can certainly handle.
// The default is 10, or every 10ms or 100 times per second.
// #define POINTING_DEVICE_TASK_THROTTLE_MS 1

// The default is 0x02, so try 0x03, then 0x04, 0x05, 0x06
// #define PMW33XX_LIFTOFF_DISTANCE 0x02