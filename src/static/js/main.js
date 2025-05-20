// Main JavaScript for Dev Legal Website

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true' || false;
            this.setAttribute('aria-expanded', !expanded);
            
            // Create mobile menu dynamically if it doesn't exist
            let mobileMenu = document.querySelector('.mobile-menu');
            
            if (!mobileMenu) {
                mobileMenu = document.createElement('div');
                mobileMenu.className = 'mobile-menu';
                
                // Clone navigation links from main nav
                const mainNav = document.querySelector('nav ul');
                if (mainNav) {
                    const navClone = mainNav.cloneNode(true);
                    mobileMenu.appendChild(navClone);
                    document.querySelector('header').appendChild(mobileMenu);
                }
            }
            
            // Toggle mobile menu visibility
            mobileMenu.classList.toggle('active');
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Close mobile menu if open
            const mobileMenu = document.querySelector('.mobile-menu');
            if (mobileMenu && mobileMenu.classList.contains('active')) {
                mobileMenu.classList.remove('active');
                
                const menuToggle = document.querySelector('.mobile-menu-toggle');
                if (menuToggle) {
                    menuToggle.setAttribute('aria-expanded', 'false');
                    
                    const icon = menuToggle.querySelector('i');
                    if (icon) {
                        icon.classList.remove('fa-times');
                        icon.classList.add('fa-bars');
                    }
                }
            }
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Adjust for header height
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Form submission handling with AJAX
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // In a real implementation, you would send the form data to the server
            // For now, just show a success message
            const formType = form.classList.contains('newsletter-form') ? 'newsletter' : 
                            form.classList.contains('contact-form') ? 'contact' : 'form';
            
            // Create success message
            const successMessage = document.createElement('div');
            successMessage.className = 'success-message';
            successMessage.textContent = formType === 'newsletter' ? 
                'Thank you for subscribing to our newsletter!' : 
                'Thank you for your message. We will get back to you soon!';
            
            // Replace form with success message
            form.innerHTML = '';
            form.appendChild(successMessage);
        });
    });
    
    // Blog search form validation
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('.search-input');
            if (searchInput && searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.classList.add('error');
                
                // Remove error class after 2 seconds
                setTimeout(() => {
                    searchInput.classList.remove('error');
                }, 2000);
            }
        });
    }
    
    // Comment form handling
    const commentForm = document.querySelector('.comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // In a real implementation, you would send the comment data to the server
            // For now, just show a success message
            const successMessage = document.createElement('div');
            successMessage.className = 'success-message';
            successMessage.textContent = 'Thank you for your comment. It will be reviewed and published soon.';
            
            // Replace form with success message
            commentForm.innerHTML = '';
            commentForm.appendChild(successMessage);
        });
    }
});
