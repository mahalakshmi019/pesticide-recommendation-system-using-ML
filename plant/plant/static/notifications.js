// PlantCare Notification System
// Include this script in all pages to enable real-time browser notifications

(function() {
    // Register Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(registration => {
                console.log('[PlantCare] Service Worker registered successfully');
            })
            .catch(error => {
                console.warn('[PlantCare] Service Worker registration failed:', error);
            });
    }

    // Notification Polling - Check for new notifications every 5 seconds
    let lastNotificationId = localStorage.getItem('lastNotificationId') || 0;
    
    function pollNotifications() {
        if (!('Notification' in window)) {
            console.log('[PlantCare] Browser does not support notifications');
            return;
        }

        if (Notification.permission !== 'granted') {
            console.log('[PlantCare] Notification permission not granted:', Notification.permission);
            return;
        }

        // Check for unread notifications
        fetch('/api/notifications/unread')
            .then(r => r.json())
            .then(data => {
                console.log('[PlantCare] Unread count:', data.count);
                if (data.count > 0) {
                    // Fetch recent notifications
                    fetch('/api/notifications/list')
                        .then(r => r.json())
                        .then(notifData => {
                            console.log('[PlantCare] Fetched notifications:', notifData.notifications ? notifData.notifications.length : 0);
                            if (notifData.success && notifData.notifications && notifData.notifications.length > 0) {
                                // Process notifications
                                notifData.notifications.forEach(notif => {
                                    console.log('[PlantCare] Checking notif ID:', notif.id, 'last:', lastNotificationId, 'read:', notif.is_read);
                                    // Only show if newer than the last shown notification and not read
                                    if (notif.id > lastNotificationId && !notif.is_read) {
                                        console.log('[PlantCare] Showing notification:', notif.title);
                                        showBrowserNotification(notif);
                                        lastNotificationId = notif.id;
                                        localStorage.setItem('lastNotificationId', lastNotificationId);
                                    }
                                });
                            }
                        })
                        .catch(e => console.error('[PlantCare] List fetch error:', e));
                }
            })
            .catch(e => console.error('[PlantCare] Unread fetch error:', e));
    }

    function showBrowserNotification(notification) {
        const options = {
            body: notification.message || 'You have a new alert',
            icon: '/static/images/logo.png',
            badge: '/static/images/badge.png',
            tag: 'plantcare-alert-' + notification.id,
            requireInteraction: true,
            actions: [
                {
                    action: 'view',
                    title: 'View',
                    icon: '/static/images/open-icon.png'
                },
                {
                    action: 'close',
                    title: 'Dismiss',
                    icon: '/static/images/close-icon.png'
                }
            ]
        };

        // Use Service Worker if available, otherwise use standard notification
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'SHOW_NOTIFICATION',
                title: notification.title || 'PlantCare Alert',
                options: options
            });
        } else {
            // Fallback to standard notification API
            new Notification(notification.title || 'PlantCare Alert', options);
        }

        console.log('[PlantCare] Browser notification shown:', notification.title);
    }

    // Start polling when page loads
    document.addEventListener('DOMContentLoaded', function() {
        // Start polling immediately
        pollNotifications();
        // Then poll every 5 seconds
        setInterval(pollNotifications, 5000);
    });

    // Also poll after page becomes visible (when user returns to tab)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            pollNotifications();
        }
    });

    // Expose functions to window for manual triggering
    window.PlantCareNotifications = {
        requestPermission: function() {
            if (!('Notification' in window)) {
                alert('Your browser does not support notifications');
                return;
            }

            if (Notification.permission === 'granted') {
                alert('Notifications are already enabled');
                return;
            }

            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    // Save permission status
                    fetch('/api/notifications/permission', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    alert('Browser notifications enabled!');
                    // Start polling immediately
                    pollNotifications();
                } else if (permission === 'denied') {
                    alert('Notifications disabled. You can enable them in browser settings.');
                }
            });
        },

        checkNow: function() {
            console.log('[PlantCare] Manual notification check triggered');
            pollNotifications();
        },

        getStatus: function() {
            return {
                supported: 'Notification' in window,
                permission: 'Notification' in window ? Notification.permission : 'N/A',
                serviceWorkerActive: 'serviceWorker' in navigator && navigator.serviceWorker.controller !== null
            };
        }
    };

    console.log('[PlantCare] Notification system initialized');
})();
