# Agent Instructions

## ACF Field Configuration

All ACF field groups must have `show_in_rest: 0` for free ACF plugin compatibility. The `group` field type (ACF PRO feature) works with this setting.

**Current setting: `show_in_rest: 0`** (required for free ACF)

Toggle commands:
- Free ACF: `sed -i 's/"show_in_rest": 1/"show_in_rest": 0/g' acf-json/*.json`
- ACF Pro: `sed -i 's/"show_in_rest": 0/"show_in_rest": 1/g' acf-json/*.json`