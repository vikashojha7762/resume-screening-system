import { MatchResult } from '../types';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import * as XLSX from 'xlsx';

export const exportToCSV = (data: MatchResult[], filename: string = 'candidates') => {
  const csvData = data.map((result) => ({
    Rank: result.rank || 'N/A',
    'Candidate ID': result.candidate_id,
    'Overall Score': result.overall_score,
    'Skills Score': result.scores_json?.skills ? (result.scores_json.skills * 100).toFixed(1) + '%' : 'N/A',
    'Experience Score': result.scores_json?.experience ? (result.scores_json.experience * 100).toFixed(1) + '%' : 'N/A',
    'Education Score': result.scores_json?.education ? (result.scores_json.education * 100).toFixed(1) + '%' : 'N/A',
  }));

  const ws = XLSX.utils.json_to_sheet(csvData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Candidates');
  XLSX.writeFile(wb, `${filename}.csv`);
};

export const exportToExcel = (data: MatchResult[], filename: string = 'candidates') => {
  const excelData = data.map((result) => ({
    Rank: result.rank || 'N/A',
    'Candidate ID': result.candidate_id,
    'Overall Score': result.overall_score,
    'Skills Score': result.scores_json?.skills ? (result.scores_json.skills * 100).toFixed(1) + '%' : 'N/A',
    'Experience Score': result.scores_json?.experience ? (result.scores_json.experience * 100).toFixed(1) + '%' : 'N/A',
    'Education Score': result.scores_json?.education ? (result.scores_json.education * 100).toFixed(1) + '%' : 'N/A',
  }));

  const ws = XLSX.utils.json_to_sheet(excelData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Candidates');
  XLSX.writeFile(wb, `${filename}.xlsx`);
};

export const exportToPDF = (data: MatchResult[], jobTitle: string, filename: string = 'candidates') => {
  const doc = new jsPDF();
  
  doc.setFontSize(18);
  doc.text('Candidate Match Results', 14, 22);
  doc.setFontSize(12);
  doc.text(`Job: ${jobTitle}`, 14, 30);
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 36);

  const tableData = data.map((result) => [
    result.rank || 'N/A',
    result.candidate_id.substring(0, 8),
    `${result.overall_score.toFixed(1)}%`,
    result.scores_json?.skills ? `${((result.scores_json.skills as number) * 100).toFixed(1)}%` : 'N/A',
    result.scores_json?.experience ? `${((result.scores_json.experience as number) * 100).toFixed(1)}%` : 'N/A',
    result.scores_json?.education ? `${((result.scores_json.education as number) * 100).toFixed(1)}%` : 'N/A',
  ]);

  (doc as any).autoTable({
    head: [['Rank', 'Candidate ID', 'Overall Score', 'Skills', 'Experience', 'Education']],
    body: tableData,
    startY: 45,
  });

  doc.save(`${filename}.pdf`);
};

