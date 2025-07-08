import React, { useState, useEffect } from 'react';

const defaultMessages = [
    "Calculating Mbappé's offsides...",
    "Counting the number of times Lamine Yamal cut inside...",
    "Analyzing Vinícius Jr.'s dribbles...",
    "Tallying Rodrygo's sprints...",
    "Measuring Pedri's touches..."
];

export default function LoadingScreen({ progress }) {
    const [msgIndex, setMsgIndex] = useState(0);

    useEffect(() => {
        const msgInterval = setInterval(() => {
            setMsgIndex(i => (i + 1) % defaultMessages.length);
        }, 2000);
        return () => clearInterval(msgInterval);
    }, []);

    return (
        <div className="fixed inset-0 bg-white flex flex-col items-center justify-center z-50">
            <div className="text-2xl font-semibold text-gray-700 mb-4">
                Loading La Liga Data...
            </div>
            <div className="overflow-hidden whitespace-nowrap w-full text-center mb-6 text-gray-500">
                <div className="inline-block animate-marquee">
                    {defaultMessages[msgIndex]}
                </div>
            </div>
            <div className="w-3/4 bg-gray-200 h-2 rounded-full overflow-hidden">
                <div
                    className="h-2 bg-red-600 transition-all duration-100"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
}