class BaseLog(object):

    def __init__(self, logger=None):
        self._log_template = '{0}'
        self._logger = logger

    def _log_debug(self, message):
        if self._logger:
            self._logger.debug(message)

    def _log_info(self, message):
        if self._logger:
            self._logger.info(message)

    def _log_warning(self, message):
        if self._logger:
            self._logger.warning(message)
