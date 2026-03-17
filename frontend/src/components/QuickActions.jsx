import React from 'react';
import { Home, DollarSign, Wrench, Calendar, MessageCircle } from 'lucide-react';

const QuickActions = ({ onActionClick, disabled }) => {
    const actions = [
        {
            id: 'inventory',
            label: 'Browse Homes',
            icon: Home,
            message: "I'd like to browse your available homes",
            color: 'bg-blue-600 hover:bg-blue-700',
            description: 'See our inventory'
        },
        {
            id: 'financing',
            label: 'Financing',
            icon: DollarSign,
            message: "I'd like to learn about financing options and calculate monthly payments",
            color: 'bg-green-600 hover:bg-green-700',
            description: 'Payment calculator'
        },
        {
            id: 'service',
            label: 'Service Request',
            icon: Wrench,
            message: "I need help with a service or warranty issue on my manufactured home",
            color: 'bg-orange-600 hover:bg-orange-700',
            description: 'Warranty & repairs'
        },
        {
            id: 'appointment',
            label: 'Book Visit',
            icon: Calendar,
            message: "I'd like to schedule a visit to your showroom",
            color: 'bg-purple-600 hover:bg-purple-700',
            description: 'Visit our lot'
        }
    ];

    return (
        <div className="flex flex-wrap gap-2 mt-3 mb-1">
            {actions.map((action) => {
                const Icon = action.icon;
                return (
                    <button
                        key={action.id}
                        onClick={() => onActionClick(action.message)}
                        disabled={disabled}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-white text-sm font-medium 
              ${action.color} transition-all duration-200 shadow-sm hover:shadow-md
              disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95`}
                    >
                        <Icon size={16} />
                        <span>{action.label}</span>
                    </button>
                );
            })}
        </div>
    );
};

export default QuickActions;
