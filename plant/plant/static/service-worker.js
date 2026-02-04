// Service Worker for Push Notifications

self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(clients.claim());
});

self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    if (event.data) {
        try {
            const data = event.data.json();
            const options = {
                body: data.body || 'You have a new notification',
                icon: 'https://via.placeholder.com/192',
                badge: 'https://via.placeholder.com/72',
                tag: data.tag || 'plantcare-notification',
                requireInteraction: data.requireInteraction || true,
                actions: [
                    {
                        action: 'open',
                        title: 'Open',
                        icon: 'https://via.placeholder.com/24'
                    },
                    {
                        action: 'close',
                        title: 'Close',
                        icon: 'https://via.placeholder.com/24'
                    }
                ]
            };
            
            event.waitUntil(
                self.registration.showNotification(data.title || 'PlantCare Alert', options)
            );
        } catch (e) {
            console.error('Error parsing push notification:', e);
        }
    }
});

self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event.action);
    
    if (event.action === 'open' || !event.action) {
        event.notification.close();
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then(clientList => {
                // Check if there's already a window/tab open
                for (let i = 0; i < clientList.length; i++) {
                    if (clientList[i].url === '/' || clientList[i].url.includes('/notifications')) {
                        return clientList[i].focus();
                    }
                }
                // If not, open a new window
                if (clients.openWindow) {
                    return clients.openWindow('/notifications');
                }
            })
        );
    } else if (event.action === 'close') {
        event.notification.close();
    }
});

self.addEventListener('notificationclose', event => {
    console.log('Notification closed');
});
