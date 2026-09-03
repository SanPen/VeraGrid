# Delayed switch event

## Purpose

Represents one imported physical switch command with an explicit target FID, guarded rising-edge trigger and evaluated delay. The event remains attached to its retained switch-position mode and physical device identity.

## Fields

- **Output mode**: retained switch-position mode written by the event.
- **Guard**: expression that enables trigger detection.
- **Trigger**: expression whose rising edge arms the event.
- **Delay**: non-negative delay evaluated when the trigger rises.
- **Target device FID**: exact physical equipment identifier.
- **Target switch FID**: exact imported switch identifier.
- **Target terminal**: physical equipment terminal containing the switch.
- **Initially closed**: exported initial switch position.
- **Command closed**: switch position applied when the event fires.

## Runtime behavior

At accepted simulation boundaries, the logic detects a guarded rising edge and schedules one command at the edge time plus the evaluated delay. When that boundary is reached, it writes the commanded position to the retained mode and marks the event as fired.
