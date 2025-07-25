import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TeamSelector from '../components/TeamSelector.jsx';
import teamLogos from '../assets/teamLogos.js';
import Header from '../components/Header.jsx';

export default function LaLigaPrediction() {
    const [teams, setTeams] = useState([]);
    const [teamId, setTeamId] = useState('');
    const [nextFixtures, setNextFixtures] = useState([]);
    const [lastFixtures, setLastFixtures] = useState([]);
    const [latestFixtures, setLatestFixtures] = useState([]);
    const [latestMatchday, setLatestMatchday] = useState(null);

    useEffect(() => {
        axios.get('/api/laliga/teams')
            .then(res => setTeams(res.data))
            .catch(err => console.error('Error fetching teams:', err));

        axios.get('/api/fixtures/matchday?league=laliga')
            .then(res => {
                const { matchday, fixtures } = res.data;
                setLatestMatchday(matchday);
                setLatestFixtures(Array.isArray(fixtures) ? fixtures : []);
            })
            .catch(err => {
                console.error('Error fetching latest matchday:', err);
                setLatestMatchday(null);
                setLatestFixtures([]);
            });
    }, []);

    useEffect(() => {
        if (!teamId) return;

        axios.get(`/api/fixtures/next/${teamId}?league=laliga`)
            .then(res => setNextFixtures(Array.isArray(res.data) ? res.data : []))
            .catch(() => setNextFixtures([]));

        axios.get(`/api/fixtures/last/${teamId}?league=laliga`)
            .then(res => setLastFixtures(Array.isArray(res.data) ? res.data : []))
            .catch(() => setLastFixtures([]));
    }, [teamId]);

    return (
        <div>
            <Header />
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-4xl mx-auto">
                    <h1 className="text-4xl font-extrabold text-gray-800 mb-8 text-center">
                        ⚽ La Liga Predictor
                    </h1>

                    {/* Team Selector */}
                    <div className="bg-white rounded-2xl shadow p-8 mb-10 border-t-4 border-red-600">
                        <TeamSelector
                            label="Select Team"
                            teams={teams}
                            selectedTeam={teamId}
                            onChange={setTeamId}
                        />
                    </div>

                    {/* Next Fixtures */}
                    <div className="mt-6 bg-white rounded-2xl shadow border-t-4 border-red-600 p-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">
                            Next 5 Fixture Predictions
                        </h2>
                        {teamId ? (
                            nextFixtures.length > 0 ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                                    {nextFixtures.map((m, i) => {
                                        const home = m?.home ?? 'Unknown';
                                        const away = m?.away ?? 'Unknown';
                                        const result = m?.prediction?.result ?? '';
                                        const predLabel =
                                            result === 'Home Win' ? `${home} to win` :
                                            result === 'Away Win' ? `${away} to win` : 'Draw';

                                        return (
                                            <div key={i} className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
                                                <div className="flex flex-col items-center mb-2">
                                                    <img src={teamLogos[home]} alt={home} className="w-16 h-16 mb-1" />
                                                    <p className="text-xs text-gray-500">Home</p>
                                                    <p className="font-medium text-gray-700">{home}</p>
                                                </div>

                                                <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
                                                    <p className="text-red-600 text-sm">{predLabel}</p>
                                                </div>

                                                <div className="flex flex-col items-center mb-2">
                                                    <p className="text-xs text-gray-500">Away</p>
                                                    <p className="font-medium text-gray-700 mb-1">{away}</p>
                                                    <img src={teamLogos[away]} alt={away} className="w-16 h-16" />
                                                </div>

                                                <p className="text-xs text-gray-500">
                                                    {new Date(m?.utcDate ?? '').toLocaleDateString()}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="text-gray-500 italic">No upcoming matches scheduled.</p>
                            )
                        ) : (
                            <p className="text-gray-500 italic">Select a team to view upcoming fixtures.</p>
                        )}
                    </div>

                    {/* Last Results */}
                    <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-red-600">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">Last 5 Results</h2>
                        {teamId ? (
                            lastFixtures.length > 0 ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                                    {lastFixtures.map((m, i) => {
                                        const home = m?.home ?? 'Unknown';
                                        const away = m?.away ?? 'Unknown';
                                        const result = m?.prediction?.result ?? '';
                                        const predLabel =
                                            result === 'Home Win' ? `${home} to win` :
                                            result === 'Away Win' ? `${away} to win` : 'Draw';
                                        const score = m?.score ?? { home: '-', away: '-' };

                                        return (
                                            <div key={i} className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
                                                <div className="flex flex-col items-center mb-2">
                                                    <img src={teamLogos[home]} alt={home} className="w-16 h-16 mb-1" />
                                                    <p className="text-xs text-gray-500">Home</p>
                                                    <p className="font-medium text-gray-700">{home}</p>
                                                </div>

                                                <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
                                                    <p className="text-red-600 font-bold">{score.home} – {score.away}</p>
                                                </div>

                                                <div className="flex flex-col items-center mb-2">
                                                    <p className="text-xs text-gray-500">Away</p>
                                                    <p className="font-medium text-gray-700 mb-1">{away}</p>
                                                    <img src={teamLogos[away]} alt={away} className="w-16 h-16" />
                                                </div>

                                                <div className="border border-red-600 rounded-full px-3 py-1 mb-2 whitespace-nowrap">
                                                    <p className="text-red-600 text-sm">Predicted: {predLabel}</p>
                                                </div>

                                                <p className="text-xs text-gray-500">
                                                    {new Date(m?.utcDate ?? '').toLocaleDateString()}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="text-gray-500 italic">No recent matches found.</p>
                            )
                        ) : (
                            <p className="text-gray-500 italic">Select a team to view recent results.</p>
                        )}
                    </div>

                    {/* Matchday Fixtures */}
                    <div className="mt-6 bg-white rounded-2xl shadow p-6 border-t-4 border-red-600">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">
                            Latest Matchday {latestMatchday || ''}
                        </h2>

                        {latestFixtures.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                                {latestFixtures.map((m, i) => {
                                    const homeName = m?.homeTeam?.name ?? 'Unknown';
                                    const awayName = m?.awayTeam?.name ?? 'Unknown';
                                    const predLabel =
                                        m?.prediction?.result === 'Home Win'
                                            ? `${homeName} to win`
                                            : m?.prediction?.result === 'Away Win'
                                            ? `${awayName} to win`
                                            : 'Draw';
                                    const ft = m?.score?.fullTime ?? { home: '-', away: '-' };

                                    return (
                                        <div key={i} className="bg-white rounded-lg shadow p-6 flex flex-col items-center">
                                            <div className="flex flex-col items-center mb-2">
                                                <img src={teamLogos[homeName]} alt={homeName} className="w-16 h-16 mb-1" />
                                                <p className="text-xs text-gray-500">Home</p>
                                                <p className="font-medium text-gray-700">{homeName}</p>
                                            </div>

                                            <div className="border border-red-600 rounded-full px-4 py-2 mb-2 whitespace-nowrap">
                                                <p className="text-red-600 font-bold">{ft.home} – {ft.away}</p>
                                            </div>

                                            <div className="flex flex-col items-center mb-2">
                                                <p className="text-xs text-gray-500">Away</p>
                                                <p className="font-medium text-gray-700 mb-1">{awayName}</p>
                                                <img src={teamLogos[awayName]} alt={awayName} className="w-16 h-16" />
                                            </div>

                                            <div className="border border-red-600 rounded-full px-3 py-1 mb-2 whitespace-nowrap">
                                                <p className="text-red-600 text-sm">Predicted: {predLabel}</p>
                                            </div>

                                            <p className="text-xs text-gray-500">
                                                {new Date(m?.utcDate ?? '').toLocaleDateString()}
                                            </p>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-gray-500 italic">No matchday data available.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
