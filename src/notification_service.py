import threading
from collections import defaultdict
from enum import Enum
from queue import Queue
from typing import Dict, List, Optional
import time
from threading import Lock

class NotificationType(Enum):
    ORDER_PLACED = "order_placed"
    ORDER_STATUS = "order_status"
    INVENTORY_ALERT = "inventory_alert"
    DELIVERY_UPDATE = "delivery_update"

class NotificationChannel(Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    SYSTEM_LOG = "system_log"

class Notification:
    def __init__(self, notification_type: NotificationType, message: str, 
                 recipient_id: str, channel: NotificationChannel = NotificationChannel.IN_APP):
        self.notification_type = notification_type
        self.message = message
        self.recipient_id = recipient_id
        self.channel = channel
        self.timestamp = time.time()

class NotificationService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.notification_queue = Queue()
        self.user_preferences: Dict[str, List[NotificationChannel]] = defaultdict(list)
        self.is_running = True
        self.notification_thread = threading.Thread(target=self._process_notifications)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        self._initialized = True

    def set_user_preferences(self, user_id: str, channels: List[NotificationChannel]):
        """Set notification preferences for a user."""
        self.user_preferences[user_id] = channels

    def send_notification(self, notification: Notification):
        """Queue a notification for processing."""
        self.notification_queue.put(notification)

    def _process_notifications(self):
        """Process notifications in the queue with retry mechanism."""
        while self.is_running:
            try:
                if not self.notification_queue.empty():
                    notification = self.notification_queue.get_nowait()
                    retry_count = 0
                    max_retries = 3
                    retry_delay = 1  # Initial delay in seconds

                    while retry_count < max_retries:
                        try:
                            self._dispatch_notification(notification)
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count == max_retries:
                                print(f"Failed to process notification after {max_retries} attempts: {e}")
                                # Could implement a dead letter queue here for failed notifications
                            else:
                                print(f"Retry {retry_count} for notification: {e}")
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff

                    self.notification_queue.task_done()
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Critical error in notification processing: {e}")
                time.sleep(1)  # Prevent tight error loops

    def _dispatch_notification(self, notification: Notification):
        """Dispatch notification through appropriate channel."""
        # Get user's preferred channels or use default
        channels = self.user_preferences.get(
            notification.recipient_id, 
            [NotificationChannel.IN_APP, NotificationChannel.SYSTEM_LOG]
        )

        if notification.channel in channels:
            self._send_to_channel(notification)

    def _send_to_channel(self, notification: Notification):
        """Send notification through specified channel."""
        if notification.channel == NotificationChannel.IN_APP:
            print(f"[IN-APP] {notification.recipient_id}: {notification.message}")
        elif notification.channel == NotificationChannel.EMAIL:
            print(f"[EMAIL] {notification.recipient_id}: {notification.message}")
        elif notification.channel == NotificationChannel.SMS:
            print(f"[SMS] {notification.recipient_id}: {notification.message}")
        elif notification.channel == NotificationChannel.SYSTEM_LOG:
            print(f"[SYSTEM] {notification.message}")

    def stop(self):
        """Stop the notification service."""
        self.is_running = False
        if self.notification_thread.is_alive():
            self.notification_thread.join()