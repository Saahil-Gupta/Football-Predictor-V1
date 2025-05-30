import React from 'react';
import teamLogos from '../assets/teamLogos.js';

export default function PredictionCard({ prediction, loading }) {
    if (!prediction && !loading) {
        return null;
    }

    return (
        <div className="mt-6 bg-white border-t-4 border-[#E30613] text-center rounded-2xl py-6 px-4 shadow-lg animate-slide-in">
            {loading ? (
                <p className="text-lg font-semibold text-gray-600">Loading prediction...</p>
            ) : (
                <>
                    <div className="flex justify-center items-center mb-4">
                        <img
                            src={teamLogos[prediction]}
                            alt={prediction}
                            className="w-16 h-16 rounded-full shadow-md border-2 border-[#E30613]"
                        />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 mb-2">Predicted Winner</h3>
                    <p className="text-3xl font-extrabold text-[#E30613]">{prediction}</p>
                </>
            )}
        </div>
    );
}
