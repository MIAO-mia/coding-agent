// Enhanced citation copying with visual feedback
function copyCitation(elementId) {
    const preElement = document.getElementById(elementId);
    if (!preElement) {
        console.error('Element not found:', elementId);
        return;
    }
    
    const text = preElement.innerText;
    const button = event.target.closest('.copy-button');
    
    // Visual feedback
    if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.style.background = 'linear-gradient(45deg, #27ae60, #2ecc71)';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = 'linear-gradient(45deg, #1abc9c, #3498db)';
        }, 2000);
    }
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showNotification('Citation copied to clipboard successfully!', 'success');
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
                showNotification('Error copying citation. Please try again.', 'error');
            });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Citation copied to clipboard!', 'success');
        } catch (err) {
            console.error('Fallback copy failed: ', err);
            showNotification('Copy failed. Please select and copy manually.', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Show notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles if not already present
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 10px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                transform: translateX(150%);
                transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            .notification.success { background: linear-gradient(45deg, #27ae60, #2ecc71); }
            .notification.error { background: linear-gradient(45deg, #e74c3c, #c0392b); }
            .notification.info { background: linear-gradient(45deg, #3498db, #2980b9); }
            .notification.show { transform: translateX(0); }
            .notification i { font-size: 1.2rem; }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Auto-submit date picker with better UX
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            // Add loading effect
            const form = this.form;
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            submitBtn.disabled = true;
            
            // Submit form
            setTimeout(() => {
                form.submit();
            }, 500);
        });
    }
    
    // Add hover effect to paper items
    const paperItems = document.querySelectorAll('.paper-item');
    paperItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Smooth scroll to top
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.id = 'scrollToTop';
    scrollToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollToTopBtn.title = 'Scroll to top';
    document.body.appendChild(scrollToTopBtn);
    
    // Add styles for scroll to top button
    const scrollStyles = document.createElement('style');
    scrollStyles.textContent = `
        #scrollToTop {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, #1abc9c, #3498db);
            color: white;
            border: none;
            cursor: pointer;
            font-size: 1.2rem;
            box-shadow: 0 5px 15px rgba(26, 188, 156, 0.4);
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            z-index: 999;
        }
        #scrollToTop.show {
            opacity: 1;
            transform: translateY(0);
        }
        #scrollToTop:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(26, 188, 156, 0.6);
        }
    `;
    document.head.appendChild(scrollStyles);
    
    // Show/hide scroll to top button
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add('show');
        } else {
            scrollToTopBtn.classList.remove('show');
        }
    });
    
    // Scroll to top functionality
    scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Add confetti effect on page load (for fun)
    setTimeout(() => {
        if (!document.querySelector('.empty-state')) {
            const confetti = document.createElement('div');
            confetti.innerHTML = '🎉';
            confetti.style.cssText = `
                position: fixed;
                font-size: 2rem;
                z-index: 1000;
                opacity: 0;
                pointer-events: none;
            `;
            document.body.appendChild(confetti);
            
            // Animate confetti
            confetti.style.left = '50%';
            confetti.style.top = '50%';
            confetti.style.opacity = '1';
            confetti.style.transform = 'translate(-50%, -50%) scale(1)';
            
            setTimeout(() => {
                confetti.style.transition = 'all 1s ease';
                confetti.style.opacity = '0';
                confetti.style.transform = 'translate(-50%, -150%) scale(0.5)';
                setTimeout(() => confetti.remove(), 1000);
            }, 500);
        }
    }, 1000);
});