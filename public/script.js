const API_BASE_URL = '/api';

// Load all stocks
async function loadAllStocks() {
    try {
        const response = await fetch(`${API_BASE_URL}/stocks`);
        const stocks = await response.json();
        
        const stocksList = document.getElementById('stocksList');
        
        if (stocks.length === 0) {
            stocksList.innerHTML = '<p class="empty-state">No stocks tracked yet. Add one to get started!</p>';
            document.getElementById('stockCount').textContent = '0';
            return;
        }
        
        stocksList.innerHTML = stocks.map(stock => `
            <div class="stock-card">
                <div class="stock-header">
                    <span class="stock-symbol">${stock.symbol}</span>
                    <button class="remove-btn" onclick="removeStock('${stock.symbol}')">Remove</button>
                </div>
                <div class="stock-price">NT$${stock.price || '0.00'}</div>
                <div class="stock-details">
                    <div class="detail-row">
                        <span>Status</span>
                        <span>Tracking</span>
                    </div>
                    <div class="detail-row">
                        <span>Added</span>
                        <span>${new Date(stock.tracked_since).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="ma-120">
                    <div>120-Day MA</div>
                    <div class="ma-120-value">${stock.ma120}</div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('stockCount').textContent = stocks.length;
    } catch (error) {
        console.error('Error loading stocks:', error);
    }
}

// Add stock
async function addStock() {
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    
    if (!symbol) {
        alert('Please enter a stock symbol');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/stocks/add/${symbol}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            document.getElementById('stockSymbol').value = '';
            loadAllStocks();
            updateLastRefreshTime();
        }
    } catch (error) {
        console.error('Error adding stock:', error);
    }
}

// Remove stock
async function removeStock(symbol) {
    if (!confirm(`Remove ${symbol}?`)) return;
    
    try {
        await fetch(`${API_BASE_URL}/stocks/${symbol}`, { method: 'DELETE' });
        loadAllStocks();
    } catch (error) {
        console.error('Error removing stock:', error);
    }
}

// Refresh all stocks
async function refreshAllStocks() {
    loadAllStocks();
    updateLastRefreshTime();
}

// Update refresh time
function updateLastRefreshTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        hour12: false 
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAllStocks();
    updateLastRefreshTime();
    
    document.getElementById('stockSymbol').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addStock();
    });
});
