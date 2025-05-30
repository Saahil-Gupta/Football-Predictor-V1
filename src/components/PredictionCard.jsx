import React from 'react';
import teamLogos from '../assets/teamLogos.js';

export default function PredictionCard({ prediction, loading }) {
    if (!prediction && !loading) {
        return null;
    }

    return (
        <div className="mt-6 bg-laliga-yellow text-center rounded-2xl py-6 px-4 shadow-xl animate-slide-in">
            {loading ? (
                <p className="text-lg font-semibold text-purple-800">Loading prediction...</p>
            ) : (
                <>
                    <h3 className="text-xl font-bold text-purple-900 mb-4">Predicted Winner</h3>
                    <div className="flex justify-center items-center gap-4">
                        <img
                            src={teamLogos[prediction]}
                            alt={prediction}
                            className="w-12 h-12 rounded-full shadow-md"
                        />
                        <p className="text-2xl font-bold text-purple-950">{prediction}</p>
                    </div>
                </>
            )}
        </div>
    );
}
