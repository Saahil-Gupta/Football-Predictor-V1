import React, { useState } from 'react';
import axios from 'axios';
import TeamSelector from './components/TeamSelector.jsx';
import PredictionCard from './components/PredictionCard.jsx';

export default function App() {
    const [homeId, setHomeId] = useState('');
    const [awayId, setAwayId] = useState('');
    const [adHocPred, setAdHocPred] = useState(null);
    const [loadingPred, setLoadingPred] = useState(false);

    const handleAdHoc = async () => {
        setLoadingPred(true);
        try {
            const { data } = await axios.post('/api/predict', {
                homeId: parseInt(homeId),
                awayId: parseInt(awayId)
            });
            setAdHocPred(data);
        } catch (err) {
            console.error(err);
            setAdHocPred({ error: 'Unable to predict' });
        } finally {
            setLoadingPred(false);
        }
    };

    return (
        <div className="min-h-screen … p-6">
            <div className="max-w-3xl mx-auto">
                <h1 className="text-5xl font-extrabold … mb-6">
                    ⚽ La Liga Matchday Predictor
                </h1>

                {/* Ad-hoc Predictor */}
                <div className="bg-white/10 p-6 rounded-2xl shadow-xl mb-10 text-left">
                    <TeamSelector
                        label="Home Team"
                        selectedTeam={homeId}
                        onChange={setHomeId}
                    />
                    <TeamSelector
                        label="Away Team"
                        selectedTeam={awayId}
                        onChange={setAwayId}
                    />
                    <button
                        onClick={handleAdHoc}
                        disabled={!homeId || !awayId || homeId === awayId}
                        className="mt-4 bg-laliga-yellow text-purple-900 …"
                    >
                        Predict
                    </button>
                    <PredictionCard
                        prediction={
                            adHocPred && adHocPred.result != null
                                ? ['Home Win','Draw','Away Win'][adHocPred.result]
                                : null
                        }
                        loading={loadingPred}

                    />
                </div>

                {/* … your existing next/last fixtures UI … */}
            </div>
        </div>
    );
}
