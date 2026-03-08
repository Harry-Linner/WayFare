import { Compass, Settings, Bell } from 'lucide-react';

interface HeaderProps {
  onSettingsClick?: () => void;
  onNotificationsClick?: () => void;
}

export function Header({ onSettingsClick, onNotificationsClick }: HeaderProps) {
  const handleSettingsClick = () => {
    console.log('Settings clicked');
    onSettingsClick?.();
  };

  const handleNotificationsClick = () => {
    console.log('Notifications clicked');
    onNotificationsClick?.();
  };

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center">
          <Compass className="text-white" size={20} />
        </div>
        <span className="font-bold text-lg tracking-tight text-gray-900">WayFare</span>
        <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs font-medium ml-2 border border-gray-200">
          Agent Mode
        </span>
      </div>
      
      <div className="flex items-center space-x-4">
        <button onClick={handleNotificationsClick} className="relative p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button>
        <button onClick={handleSettingsClick} className="p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors">
          <Settings size={18} />
        </button>
        <div className="w-8 h-8 rounded-full bg-gray-300 border-2 border-white shadow-sm"></div>
      </div>
    </header>
  );
}
