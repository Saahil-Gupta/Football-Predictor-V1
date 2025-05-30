import React from 'react';

export default function TeamSelector({ label, selectedTeam, onChange }) {
    const teams = [
        'Barcelona',
        'Real Madrid',
        'Atletico Madrid',
        'Sevilla',
        'Valencia',
        'Villarreal',
        'Real Betis',
        'Athletic Club',
        'Real Sociedad',
        'Celta Vigo'
        // Add more teams as needed
    ];

    return (
        <div className="mb-6 text-left">
            <label className="block mb-2 text-lg font-semibold text-white">
                {label}
            </label>
            <select
                value={selectedTeam}
                onChange={(e) => onChange(e.target.value)}
                className="w-full px-4 py-2 rounded-lg text-purple-900 font-medium bg-laliga-yellow shadow-lg focus:outline-none"
            >
                <option value="">-- Select Team --</option>
                {teams.map((team) => (
                    <option key={team} value={team}>
                        {team}
                    </option>
                ))}
            </select>
        </div>
    );
}