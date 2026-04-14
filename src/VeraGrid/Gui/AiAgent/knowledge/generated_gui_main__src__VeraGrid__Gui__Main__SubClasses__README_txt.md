# VeraGrid GUI Main Text Resource: src/VeraGrid/Gui/Main/SubClasses/README.txt

- Original source path: `src/VeraGrid/Gui/Main/SubClasses/README.txt`
- Knowledge kind: generated plain text resource summary

## Resource Content

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0



Since version 5.0.0 VeraGrid's main GUI class
was split in many other classes that inherit
from each other linearly. This was done to
simplify the massive original class.

The subclasses inheritance order is:

BaseMainGui
ServerMain
CompiledArraysMain
DiagramsMain
DataBaseTableMain
TimeEventsMain
SimulationsMain
ResultsMain
ConfigurationMain
ScenariosMain
IoMain
ScriptingMain
VeraGridMainGUI
