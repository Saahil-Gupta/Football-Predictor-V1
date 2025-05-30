// import React from 'react';

// export default function TeamSelector({ label, selectedTeam, onChange }) {
//     const teams = [
//         'Alavés',
//         'Athletic Club',
//         'Atlético Madrid',
//         'Barcelona',
//         'Celta Vigo',
//         'Espanyol',
//         'Getafe',
//         'Girona',
//         'Las Palmas',
//         'Leganés',
//         'Mallorca',
//         'Osasuna',
//         'Rayo Vallecano',
//         'Real Betis',
//         'Real Madrid',
//         'Real Sociedad',
//         'Sevilla',
//         'Valencia',
//         'Valladolid',
//         'Villarreal'
//     ];

//     return (
//         <div className="mb-6 text-left">
//             <label className="block mb-2 text-lg font-semibold text-gray-800">
//                 {label}
//             </label>
//             <select
//                 value={selectedTeam}
//                 onChange={(e) => onChange(e.target.value)}
//                 className="w-full px-4 py-3 bg-white border-t-4 border-[#E30613] rounded-lg shadow-md font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#E30613]"
//             >
//                 <option value="" className="text-gray-500">-- Select Team --</option>
//                 {teams.map((team) => (
//                     <option key={team} value={team} className="text-gray-800">
//                         {team}
//                     </option>
//                 ))}
//             </select>
//         </div>
//     );
// }


import React from 'react';

export default function TeamSelector({ label, teams, selectedTeam, onChange }) {
    return (
        <div className="mb-6 text-left">
            <label className="block mb-2 text-lg font-semibold text-gray-800">
                {label}
            </label>
            <select
                value={selectedTeam}
                onChange={(e) => onChange(e.target.value)}
                className="w-full px-4 py-3 bg-white border-t-4 border-[#E30613] rounded-lg shadow-md font-medium text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#E30613]"
            >
                <option value="" className="text-gray-500">-- Select Team --</option>
                {teams.map((team) => (
                    <option key={team.id} value={team.id} className="text-gray-800">
                        {team.name}
                    </option>
                ))}
            </select>
        </div>
    );
}