import pytest
from unittest.mock import patch
from pydantic import ValidationError

from meet_transcriber.config import Settings


class TestSettings:
    """Test cases for Settings configuration."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()
        
        # Core settings
        assert settings.model_name == "tiny.en"
        assert settings.language == "en"
        assert settings.auth_token is None
        assert settings.max_concurrent_sessions == 10
        assert settings.host == "0.0.0.0"
        assert settings.port == 8765
        assert settings.log_level == "INFO"
        
        # N8N webhook settings
        assert settings.n8n_webhook_url is None
        assert settings.n8n_webhook_enabled is False
        assert settings.n8n_max_retries == 3
        assert settings.n8n_retry_delay == 1.0
        assert settings.n8n_backoff_factor == 2.0
        assert settings.n8n_timeout == 30.0
        
        # Transcript buffer settings
        assert settings.transcript_flush_interval == 10.0
        assert settings.transcript_max_segments_before_flush == 50
        assert settings.enable_webhook_delivery_status is True
    
    def test_environment_variable_prefix(self):
        """Test that environment variables use correct prefix."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_MODEL_NAME': 'medium.en',
            'MEET_TRANSCRIBER_LANGUAGE': 'es',
            'MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS': '20',
            'MEET_TRANSCRIBER_N8N_WEBHOOK_URL': 'https://webhook.example.com',
            'MEET_TRANSCRIBER_N8N_WEBHOOK_ENABLED': 'true',
            'MEET_TRANSCRIBER_TRANSCRIPT_FLUSH_INTERVAL': '15.0',
        }):
            settings = Settings()
            
            assert settings.model_name == "medium.en"
            assert settings.language == "es"
            assert settings.max_concurrent_sessions == 20
            assert settings.n8n_webhook_url == "https://webhook.example.com"
            assert settings.n8n_webhook_enabled is True
            assert settings.transcript_flush_interval == 15.0
    
    def test_auth_token_configuration(self):
        """Test authentication token configuration."""
        # No auth token
        with patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            assert settings.auth_token is None
        
        # With auth token
        with patch.dict('os.environ', {'MEET_TRANSCRIBER_AUTH_TOKEN': 'secret123'}):
            settings = Settings()
            assert settings.auth_token == 'secret123'
    
    def test_n8n_webhook_settings(self):
        """Test N8N webhook specific settings."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_N8N_WEBHOOK_URL': 'https://test.webhook.com',
            'MEET_TRANSCRIBER_N8N_WEBHOOK_ENABLED': 'true',
            'MEET_TRANSCRIBER_N8N_MAX_RETRIES': '5',
            'MEET_TRANSCRIBER_N8N_RETRY_DELAY': '2.0',
            'MEET_TRANSCRIBER_N8N_BACKOFF_FACTOR': '3.0',
            'MEET_TRANSCRIBER_N8N_TIMEOUT': '60.0',
        }):
            settings = Settings()
            
            assert settings.n8n_webhook_url == "https://test.webhook.com"
            assert settings.n8n_webhook_enabled is True
            assert settings.n8n_max_retries == 5
            assert settings.n8n_retry_delay == 2.0
            assert settings.n8n_backoff_factor == 3.0
            assert settings.n8n_timeout == 60.0
    
    def test_transcript_buffer_settings(self):
        """Test transcript buffer specific settings."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_TRANSCRIPT_FLUSH_INTERVAL': '20.0',
            'MEET_TRANSCRIBER_TRANSCRIPT_MAX_SEGMENTS_BEFORE_FLUSH': '100',
            'MEET_TRANSCRIBER_ENABLE_WEBHOOK_DELIVERY_STATUS': 'false',
        }):
            settings = Settings()
            
            assert settings.transcript_flush_interval == 20.0
            assert settings.transcript_max_segments_before_flush == 100
            assert settings.enable_webhook_delivery_status is False
    
    def test_host_port_configuration(self):
        """Test host and port configuration."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_HOST': '127.0.0.1',
            'MEET_TRANSCRIBER_PORT': '9000',
        }):
            settings = Settings()
            
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
    
    def test_log_level_configuration(self):
        """Test log level configuration."""
        # Valid log levels
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            with patch.dict('os.environ', {'MEET_TRANSCRIBER_LOG_LEVEL': level}):
                settings = Settings()
                assert settings.log_level == level
        
        # Case insensitive
        with patch.dict('os.environ', {'MEET_TRANSCRIBER_LOG_LEVEL': 'debug'}):
            settings = Settings()
            assert settings.log_level == 'debug'
    
    def test_type_conversion(self):
        """Test proper type conversion from environment variables."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS': '25',
            'MEET_TRANSCRIBER_PORT': '8080',
            'MEET_TRANSCRIBER_N8N_MAX_RETRIES': '10',
            'MEET_TRANSCRIBER_N8N_RETRY_DELAY': '1.5',
            'MEET_TRANSCRIBER_N8N_TIMEOUT': '45.0',
            'MEET_TRANSCRIBER_TRANSCRIPT_FLUSH_INTERVAL': '30.0',
            'MEET_TRANSCRIBER_TRANSCRIPT_MAX_SEGMENTS_BEFORE_FLUSH': '75',
        }):
            settings = Settings()
            
            # Should be converted to correct types
            assert isinstance(settings.max_concurrent_sessions, int)
            assert settings.max_concurrent_sessions == 25
            
            assert isinstance(settings.port, int)
            assert settings.port == 8080
            
            assert isinstance(settings.n8n_max_retries, int)
            assert settings.n8n_max_retries == 10
            
            assert isinstance(settings.n8n_retry_delay, float)
            assert settings.n8n_retry_delay == 1.5
            
            assert isinstance(settings.n8n_timeout, float)
            assert settings.n8n_timeout == 45.0
            
            assert isinstance(settings.transcript_flush_interval, float)
            assert settings.transcript_flush_interval == 30.0
            
            assert isinstance(settings.transcript_max_segments_before_flush, int)
            assert settings.transcript_max_segments_before_flush == 75
    
    def test_boolean_conversion(self):
        """Test boolean environment variable conversion."""
        # True values
        for true_value in ['true', 'True', 'TRUE', '1', 'yes', 'Yes']:
            with patch.dict('os.environ', {'MEET_TRANSCRIBER_N8N_WEBHOOK_ENABLED': true_value}):
                settings = Settings()
                assert settings.n8n_webhook_enabled is True
        
        # False values
        for false_value in ['false', 'False', 'FALSE', '0', 'no', 'No', '']:
            with patch.dict('os.environ', {'MEET_TRANSCRIBER_N8N_WEBHOOK_ENABLED': false_value}):
                settings = Settings()
                assert settings.n8n_webhook_enabled is False
    
    def test_invalid_integer_value(self):
        """Test handling of invalid integer values."""
        with patch.dict('os.environ', {'MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS': 'invalid'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_invalid_float_value(self):
        """Test handling of invalid float values."""
        with patch.dict('os.environ', {'MEET_TRANSCRIBER_N8N_RETRY_DELAY': 'invalid'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_invalid_boolean_value(self):
        """Test handling of invalid boolean values."""
        with patch.dict('os.environ', {'MEET_TRANSCRIBER_N8N_WEBHOOK_ENABLED': 'invalid'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_case_sensitivity(self):
        """Test case insensitive environment variable handling."""
        with patch.dict('os.environ', {
            'meet_transcriber_model_name': 'medium.en',  # lowercase
            'MEET_TRANSCRIBER_LANGUAGE': 'fr',  # uppercase
        }):
            settings = Settings()
            
            # Case insensitive, so both should work
            assert settings.model_name == "medium.en"
            assert settings.language == "fr"
    
    def test_partial_configuration(self):
        """Test configuration with only some settings provided."""
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_MODEL_NAME': 'large.en',
            'MEET_TRANSCRIBER_PORT': '9000',
        }, clear=True):
            settings = Settings()
            
            # Provided values
            assert settings.model_name == "large.en"
            assert settings.port == 9000
            
            # Default values for others
            assert settings.language == "en"
            assert settings.max_concurrent_sessions == 10
            assert settings.n8n_webhook_enabled is False
            assert settings.transcript_flush_interval == 10.0
    
    def test_configuration_validation(self):
        """Test configuration validation rules."""
        # Test reasonable bounds
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS': '1',
            'MEET_TRANSCRIBER_N8N_MAX_RETRIES': '0',
            'MEET_TRANSCRIBER_N8N_TIMEOUT': '0.1',
            'MEET_TRANSCRIBER_TRANSCRIPT_FLUSH_INTERVAL': '0.1',
        }):
            settings = Settings()
            
            assert settings.max_concurrent_sessions == 1
            assert settings.n8n_max_retries == 0
            assert settings.n8n_timeout == 0.1
            assert settings.transcript_flush_interval == 0.1
        
        # Test negative values (should be allowed by pydantic but might be clamped by business logic)
        with patch.dict('os.environ', {
            'MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS': '-1',
        }):
            settings = Settings()
            assert settings.max_concurrent_sessions == -1