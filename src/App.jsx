import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TeamSelector from './components/TeamSelector.jsx';

// LoadingScreen component
const defaultMessages = [
    "Calculating Mbappé's offsides...",
    "Counting the number of times Lamine Yamal cut inside...",
    "Analyzing Vinícius Jr.'s dribbles...",
    "Tallying Rodrygo's sprints...",
    "Measuring Pedri's touches..."
];

function LoadingScreen({ progress }) {
    const [msgIndex, setMsgIndex] = useState(0);

    useEffect(() => {
        const msgInterval = setInterval(() => {
            setMsgIndex(i => (i + 1) % defaultMessages.length);
        }, 2000);
        return () => clearInterval(msgInterval);
    }, []);

    return (
        <div className="fixed inset-0 bg-white flex flex-col items-center justify-center">
            <div className="text-2xl font-semibold text-gray-800 mb-4">Loading La Liga Data...</div>
            <marquee className="text-gray-600 mb-6" behavior="scroll" direction="left">
                {defaultMessages[msgIndex]}
            </marquee>
            <div className="w-3/4 bg-gray-200 h-2 rounded-full overflow-hidden">
                <div
                    className="h-2 bg-[#E30613]"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
}


export default function App() {
    const [teams, setTeams] = useState([]);
    const [teamId, setTeamId] = useState('');
    const [nextFixtures, setNextFixtures] = useState([]);
    const [lastFixtures, setLastFixtures] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [progress, setProgress] = useState(0);

    // Fetch team list on mount
    // Initial load: fetch teams and enforce a 6-second loading screen
    useEffect(() => {
        const start = Date.now();
        const interval = setInterval(() => {
            const elapsed = Date.now() - start;
            setProgress(Math.min(100, (elapsed / 6000) * 100));
        }, 100);

        // Hide loading after 6 seconds
        const loaderTimeout = setTimeout(() => {
            clearInterval(interval);
            setProgress(100);
            setIsLoading(false);
        }, 10000);

        // Fetch teams
        axios.get('/api/teams')
            .then(res => setTeams(res.data))
            .catch(err => console.error('Error fetching teams:', err));

        return () => {
            clearInterval(interval);
            clearTimeout(loaderTimeout);
        };
    }, []);

    // Fetch fixtures when a valid teamId is selected
    useEffect(() => {
        if (!teamId) {
            setNextFixtures([]);
            setLastFixtures([]);
            return;
        }
        console.log('Selected teamId:', teamId);
        axios.get(`/api/fixtures/next/${teamId}`)
            .then(res => {
                let data = res.data;
                if (!Array.isArray(data)) data = [];
                console.log('Next fixtures:', data);
                setNextFixtures(data);
            })
            .catch(err => {
                console.error('Error fetching next fixtures:', err);
                setNextFixtures([]);
            });

        axios.get(`/api/fixtures/last/${teamId}`)
            .then(res => {
                let data = res.data;
                if (!Array.isArray(data)) data = [];
                console.log('Last fixtures:', data);
                setLastFixtures(data);
            })
            .catch(err => {
                console.error('Error fetching last fixtures:', err);
                setLastFixtures([]);
            });
    }, [teamId]);

    if (isLoading) {
        return <LoadingScreen progress={progress} />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-white to-gray-100 p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-4xl font-extrabold text-gray-800 mb-8 text-center">
                    ⚽ La Liga Match predictor
                </h1>

                <div className="bg-white rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-8 mb-10">
                    <TeamSelector
                        label="Select Team"
                        teams={teams}
                        selectedTeam={teamId}
                        onChange={setTeamId}
                    />
                </div>

                {/* Next Fixtures */}
                <div className="mt-6 bg-white rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-6">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Next 5 Fixture Predictions</h2>
                    {teamId ? (
                        nextFixtures.length > 0 ? (
                            nextFixtures.map((m, i) => (
                                <div key={i} className="mb-4">
                                    <p className="font-medium text-gray-700">
                                        {new Date(m.utcDate).toLocaleDateString()} – {m.home} vs {m.away}
                                    </p>
                                    {m.prediction && (
                                        <p className="text-[#E30613]">
                                            Prediction: {['Home Win','Draw','Away Win'][m.prediction.result]} ({(m.prediction.confidence[m.prediction.result] * 100).toFixed(1)}%)
                                        </p>
                                    )}
                                </div>
                            ))
                        ) : (
                            <p className="text-gray-600 italic">No upcoming matches scheduled.</p>
                        )
                    ) : (
                        <p className="text-gray-500 italic">Select a team to view upcoming fixtures.</p>
                    )}
                </div>

                {/* Last Fixtures */}
                <div className="mt-6 bg-white rounded-2xl shadow-2xl border-t-4 border-[#E30613] p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Last 5 Results</h2>
                {teamId ? (
                    lastFixtures.length > 0 ? (
                    lastFixtures.map((m, i) => {
                        const labels = ['Home Win','Draw','Away Win'];

                        // Build a human-friendly label
                        let predLabel;
                        if (m.prediction?.result === 'Home Win') {
                        predLabel = `${m.home} to win`;
                        } else if (m.prediction?.result === 'Away Win') {
                        predLabel = `${m.away} to win`;
                        } else {
                        predLabel = 'Draw';
                        }

                        return (
                        <div key={i} className="mb-4">
                            <p className="font-medium text-gray-700">
                            {new Date(m.utcDate).toLocaleDateString()} – {m.home} {m.score.home}-{m.score.away} {m.away}
                            </p>
                            {m.prediction?.result && (
                            <p className="text-[#E30613] italic">
                                Predicted: {predLabel} 
                            </p>
                            )}
                        </div>
                        );
                    })
                    ) : (
                    <p className="text-gray-600 italic">No recent matches found.</p>
                    )
                ) : (
                    <p className="text-gray-500 italic">Select a team to view recent results.</p>
                )}
                </div>
            </div>
        </div>
    );
}
