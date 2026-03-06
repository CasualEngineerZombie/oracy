const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function convertHTMLToPDF() {
    const htmlFile = path.join(__dirname, '..', 'Oracy-AI-Planning-Documentation.html');
    const pdfFile = path.join(__dirname, '..', 'Oracy-AI-Planning-Documentation.pdf');
    
    if (!fs.existsSync(htmlFile)) {
        console.error('HTML file not found:', htmlFile);
        process.exit(1);
    }
    
    console.log('Launching browser...');
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    try {
        const page = await browser.newPage();
        
        const htmlPath = 'file:///' + path.resolve(htmlFile).replace(/\\/g, '/');
        console.log('Loading HTML:', htmlPath);
        
        await page.goto(htmlPath, {
            waitUntil: 'networkidle0',
            timeout: 60000
        });
        
        // Wait for fonts to load
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('Generating PDF...');
        await page.pdf({
            path: pdfFile,
            format: 'A4',
            printBackground: true,
            margin: {
                top: '20mm',
                right: '20mm',
                bottom: '20mm',
                left: '20mm'
            },
            displayHeaderFooter: true,
            headerTemplate: '<div></div>',
            footerTemplate: `
                <div style="font-size: 9px; width: 100%; text-align: center; color: #666; padding: 0 20mm;">
                    Page <span class="pageNumber"></span> of <span class="totalPages"></span>
                </div>
            `
        });
        
        const stats = fs.statSync(pdfFile);
        const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
        
        console.log('\n[SUCCESS] PDF created successfully!');
        console.log('Location:', pdfFile);
        console.log('File size:', fileSizeMB, 'MB');
        
    } catch (error) {
        console.error('\n[ERROR] Failed to create PDF:', error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
}

convertHTMLToPDF();
