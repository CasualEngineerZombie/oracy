const fs = require('fs');
const path = require('path');
const { mdToPdf } = require('md-to-pdf');

async function combineAndConvert() {
  const planningDir = path.join(__dirname, '..', 'planning');
  const outputFile = path.join(__dirname, '..', 'Oracy-AI-Planning-Documentation.pdf');
  
  // Order of files
  const files = [
    'index.md',
    '01-architecture-overview.md',
    '02-tech-stack.md',
    '03-aws-infrastructure.md',
    '04-ai-ml-pipeline.md',
    '05-backend-structure.md',
    '06-frontend-structure.md',
    '07-database-schema.md',
    '08-security-compliance.md',
    '09-development-roadmap.md',
    '10-deployment-strategy.md'
  ];
  
  let combinedContent = `# Oracy AI - Planning Documentation\n\n`;
  combinedContent += `**Generated:** ${new Date().toISOString()}\n\n`;
  combinedContent += `---\n\n`;
  
  for (const file of files) {
    const filePath = path.join(planningDir, file);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      combinedContent += content;
      combinedContent += '\n\n---\n\n';
      console.log(`Added: ${file}`);
    } else {
      console.log(`Skipped (not found): ${file}`);
    }
  }
  
  // Write combined markdown temporarily
  const tempMdFile = path.join(__dirname, '..', 'temp-combined.md');
  fs.writeFileSync(tempMdFile, combinedContent);
  
  // Convert to PDF
  console.log('\nConverting to PDF...');
  
  const pdf = await mdToPdf({ path: tempMdFile }, {
    dest: outputFile,
    pdf_options: {
      printBackground: true,
      format: 'A4',
      margin: {
        top: '20mm',
        right: '20mm',
        bottom: '20mm',
        left: '20mm'
      }
    },
    stylesheet: [
      'https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css'
    ],
    css: `
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
      pre { background: #f6f8fa; padding: 16px; overflow: auto; }
      code { font-family: Consolas, Monaco, monospace; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background-color: #f2f2f2; }
      img { max-width: 100%; }
      h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
      h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; }
    `
  });
  
  // Clean up temp file
  fs.unlinkSync(tempMdFile);
  
  if (pdf) {
    console.log(`\n✅ PDF created successfully: ${outputFile}`);
    console.log(`File size: ${(fs.statSync(outputFile).size / 1024 / 1024).toFixed(2)} MB`);
  }
}

combineAndConvert().catch(console.error);
