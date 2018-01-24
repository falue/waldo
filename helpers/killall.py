#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
os.system("kill -9 `ps -aef | grep 'remote' | grep -v grep | awk '{print $2}'`")
os.system("kill -9 `ps -aef | grep 'shutdown_button' | grep -v grep | awk '{print $2}'`")
os.system("kill -9 `ps -aef | grep 'numpad_listener' | grep -v grep | awk '{print $2}'`")
os.system("kill -9 `ps -aef | grep 'main' | grep -v grep | awk '{print $2}'`")
