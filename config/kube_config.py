# Configure parameters for generated Circuit Breaker
class CIRCUIT_BREAKER_CONFIG:
    MAX_CONNECTIONS: int = 5
    HTTP_1_MAX_PENDING_REQUESTS: int = 3
    MAX_REQUESTS_PER_CONNECTION: int = 3
    CONSECUTIVE_5XX_ERRORS: int = 2
    INTERVAL: str = "1s"
    BASE_EJECTION_TIME: str = "3m"  # (example: 3m)
    MAX_EJECTION_PERCENT: int = 20
