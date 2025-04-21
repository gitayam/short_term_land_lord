@bp.route('/property/<token>/guide', methods=['GET'])
def public_guide_book(token):
    """Public access to a property's guide book via token."""
    property = Property.query.filter_by(guide_book_token=token).first_or_404()
    
    # Get recommendations for this property
    recommendations = RecommendationBlock.query.filter_by(
        property_id=property.id
    ).order_by(RecommendationBlock.created_at.desc()).all()
    
    return render_template(
        'property/public_guide.html',
        property=property,
        recommendations=recommendations
    ) 