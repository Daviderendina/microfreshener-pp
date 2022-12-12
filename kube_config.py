# Configure parameters for generated Circuit Breaker
class CIRCUIT_BREAKER_CONFIG:
    MAX_CONNECTIONS: int = None
    HTTP_1_MAX_PENDING_REQUESTS: int = None
    MAX_REQUESTS_PER_CONNECTION: int = None
    CONSECUTIVE_5XX_ERRORS: int = None
    INTERVAL: str = None  # (example: 1s for 1 second)
    BASE_EJECTION_TIME: str = None  # (example: 3m)
    MAX_EJECTION_PERCENT: int = None
