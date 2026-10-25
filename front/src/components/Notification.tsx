import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { BellRing, X } from "lucide-react";

type Notification = {
  id: number;
  message: string;
};

type NotifyFn = (message: string) => void;

const NotificationContext = createContext<NotifyFn | null>(null);

const AUTO_DISMISS_MS = 5000;
const MAX_VISIBLE = 3;

export function useNotification(): NotifyFn {
  const notify = useContext(NotificationContext);

  if (!notify) {
    throw new Error("useNotification deve ser usado dentro de <NotificationProvider>.");
  }

  return notify;
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const nextId = useRef(0);
  const timers = useRef<number[]>([]);

  const dismiss = useCallback((id: number) => {
    setNotifications((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback<NotifyFn>(
    (message: string) => {
      nextId.current += 1;
      const id = nextId.current;

      setNotifications((current) => [...current, { id, message }].slice(-MAX_VISIBLE));

      const timerId = window.setTimeout(() => {
        timers.current = timers.current.filter((t) => t !== timerId);
        dismiss(id);
      }, AUTO_DISMISS_MS);

      timers.current.push(timerId);
    },
    [dismiss],
  );

  useEffect(() => {
    const pendingTimers = timers.current;

    return () => {
      pendingTimers.forEach((timerId) => window.clearTimeout(timerId));
    };
  }, []);

  const value = useMemo(() => notify, [notify]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <div
        className="notification-region"
        role="region"
        aria-label="Notificações do sistema"
      >
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className="notification"
            role="status"
            aria-live="polite"
          >
            <BellRing className="notification-icon" size={18} aria-hidden="true" />
            <p className="notification-message">{notification.message}</p>
            <button
              type="button"
              className="notification-close"
              onClick={() => dismiss(notification.id)}
              aria-label="Fechar notificação"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}
