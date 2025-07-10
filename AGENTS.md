## Agent Instructions and Conventions

This document provides guidance for AI agents working with this codebase.

### Project Overview

The project aims to integrate Angel One SmartAPI as a data provider. It includes modules for:
- Interacting with the Angel One API (`angelone_data_provider.py`). (Currently uses placeholders due to difficulties accessing live documentation; assumes `smartapi-python` library usage).
- Managing user settings, particularly data refresh rates (`settings_manager.py`).
- Orchestrating data fetching, including manual and scheduled refreshes (`data_manager.py`).

### Key Modules and Their Purpose

1.  **`angelone_data_provider.py`**:
    *   **Purpose**: Abstract away the direct calls to the Angel One SmartAPI.
    *   **Current State**: Contains placeholder methods for authentication, fetching LTP, portfolio, positions, and P&L. These are based on educated guesses about how a typical trading API SDK would work.
    *   **Future Work**: If actual `smartapi-python` library details or comprehensive documentation becomes available, this module will need to be updated to use the correct library calls, parameters, and response handling. Error handling for API-specific exceptions should also be fleshed out.

2.  **`settings_manager.py`**:
    *   **Purpose**: Load, save, and manage user-configurable settings. Currently, this is focused on the data refresh rate.
    *   **Storage**: Uses a `user_settings.json` file.
    *   **Refresh Rates**: Supports 'manual', '30s', '1m', '2m', '5m', '10m', '15m'.

3.  **`data_manager.py`**:
    *   **Purpose**: Core logic for data handling. Uses `angelone_data_provider` to fetch data and `settings_manager` to determine refresh behavior.
    *   **Features**:
        *   Authentication management (currently basic).
        *   Manual data refresh.
        *   Scheduled data refresh using a separate thread.
        *   A simple `DataStore` for holding fetched data in memory.
    *   **Authentication Note**: The current authentication flow is simplified. A real application would require secure handling of API keys, client codes, passwords/PINs, and TOTP. The `DataManager` would need to be properly integrated into such a flow.
    *   **Tracked Instruments**: The `tracked_instruments` list in `DataManager` is currently static. In a real application, this would likely be dynamic, based on user input or other criteria.

### Development and Testing

*   **Unit Tests**:
    *   Tests are located in `test_*.py` files (e.g., `test_settings_manager.py`, `test_data_manager.py`).
    *   Run tests using `python -m unittest discover -s . -p "test_*.py"`.
    *   `angelone_data_provider.py` tests currently mock out the actual API interaction due to lack of direct API access during development.
    *   `data_manager.py` tests involve mocking time, threading events, and the data provider to test its logic in isolation.
*   **Python Version**: Assumed to be Python 3.x.
*   **Dependencies**:
    *   The code currently has no external library dependencies explicitly installed other than what might be implied by `smartapi-python` (which itself is not yet integrated). If `smartapi-python` is formally added, its dependencies will also need to be managed (e.g., via a `requirements.txt` file).

### Future Considerations / Integration Points

*   **UI Integration**:
    *   A UI would need to provide input for authentication (especially TOTP).
    *   Refresh buttons on relevant pages should call `data_manager.manual_refresh()`.
    *   A settings panel should allow users to select refresh rates, which would call `settings_manager.set_refresh_rate()` and then `data_manager.update_refresh_settings()`.
    *   UI components will need to observe the `data_manager.data_store` (or a more robust state management solution) to display updated data.
*   **Error Handling**: Robust error handling for API calls (network issues, rate limits, invalid responses, authentication failures) needs to be implemented in `angelone_data_provider.py` and propagated appropriately.
*   **Configuration Management**: API keys and other sensitive credentials should be managed securely (e.g., environment variables, dedicated secrets management) and not hardcoded.
*   **Logging**: Implement comprehensive logging for better traceability and debugging.
*   **`smartapi-python` Integration**: The most significant next step for `angelone_data_provider.py` is to integrate the actual `smartapi-python` library once its usage is clear. This will involve replacing all mock/placeholder logic with real API calls.

### Agent Coding Conventions

*   Follow PEP 8 Python style guidelines.
*   Write clear and concise docstrings for modules, classes, and functions.
*   Ensure unit tests are written for new functionality and existing tests pass after changes.
*   If modifying core logic in `data_manager.py` or `angelone_data_provider.py`, pay close attention to the existing mock structures in the tests and update them as needed.
*   When dealing with threading or time-sensitive operations in `data_manager.py`, ensure tests adequately cover these aspects, potentially requiring advanced mocking techniques as seen in `test_data_manager.py`.Tool output for `create_file_with_block`:
