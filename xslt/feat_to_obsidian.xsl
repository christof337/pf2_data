<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" encoding="UTF-8"/>

  <!-- Template réutilisable : chiffre d'action → libellé pf2e-stats -->
  <xsl:template name="action-label">
    <xsl:param name="n"/>
    <xsl:choose>
      <xsl:when test="$n='1'">one-action</xsl:when>
      <xsl:when test="$n='2'">two-actions</xsl:when>
      <xsl:when test="$n='3'">three-actions</xsl:when>
      <xsl:when test="$n='9' or $n='R' or $n='reaction'">reaction</xsl:when>
      <xsl:when test="$n='0' or $n='free'">free-action</xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/feats/feat">
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:text>&#96;&#96;&#96;pf2e-stats&#10;</xsl:text>
    <xsl:text>#### [[fr]]&#10;</xsl:text>

    <!-- # NOM `[action]` -->
    <xsl:text># </xsl:text><xsl:value-of select="name"/>
    <xsl:if test="actions">
      <xsl:text> &#96;[</xsl:text>
      <xsl:call-template name="action-label">
        <xsl:with-param name="n" select="actions"/>
      </xsl:call-template>
      <xsl:text>]&#96;</xsl:text>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>

    <!-- ## DON N / ACTION / RÉACTION / ACTION LIBRE -->
    <xsl:text>## </xsl:text>
    <xsl:choose>
      <xsl:when test="@type='action'">ACTION</xsl:when>
      <xsl:when test="@type='reaction'">RÉACTION</xsl:when>
      <xsl:when test="@type='action-libre'">ACTION LIBRE</xsl:when>
      <xsl:otherwise>DON</xsl:otherwise>
    </xsl:choose>
    <xsl:if test="level">
      <xsl:text> </xsl:text><xsl:value-of select="level"/>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>

    <xsl:text>----&#10;</xsl:text>

    <!-- Traits -->
    <xsl:if test="traits/trait">
      <xsl:for-each select="traits/trait">
        <xsl:text>==</xsl:text><xsl:value-of select="."/><xsl:text>==</xsl:text>
        <xsl:if test="position() != last()"><xsl:text> </xsl:text></xsl:if>
      </xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>

    <!-- Champs mécaniques + 2e séparateur (seulement si au moins un champ est présent) -->
    <xsl:if test="prerequisites or skills or frequency or trigger or requirement">
      <xsl:if test="prerequisites">
        <xsl:text>**Prérequis** </xsl:text><xsl:value-of select="prerequisites"/><xsl:text>&#10;</xsl:text>
      </xsl:if>
      <xsl:if test="skills">
        <xsl:text>**Compétences** </xsl:text>
        <xsl:for-each select="skills/skill">
          <xsl:value-of select="."/>
          <xsl:if test="position() != last()">, </xsl:if>
        </xsl:for-each>
        <xsl:text>&#10;</xsl:text>
      </xsl:if>
      <xsl:if test="frequency">
        <xsl:text>**Fréquence** </xsl:text><xsl:value-of select="frequency"/><xsl:text>&#10;</xsl:text>
      </xsl:if>
      <xsl:if test="trigger">
        <xsl:text>**Déclencheur** </xsl:text><xsl:value-of select="trigger"/><xsl:text>&#10;</xsl:text>
      </xsl:if>
      <xsl:if test="requirement">
        <xsl:text>**Conditions** </xsl:text><xsl:value-of select="requirement"/><xsl:text>&#10;</xsl:text>
      </xsl:if>
      <xsl:text>---- &#10;</xsl:text>
    </xsl:if>

    <!-- Description -->
    <xsl:value-of select="description"/>
    <xsl:text> &#10;</xsl:text>

    <!-- Degrés de succès -->
    <xsl:if test="successDegrees/criticalSuccess">
      <xsl:text>**Succès critique.** </xsl:text><xsl:value-of select="successDegrees/criticalSuccess"/><xsl:text>  &#10;</xsl:text>
    </xsl:if>
    <xsl:if test="successDegrees/success">
      <xsl:text>**Succès.** </xsl:text><xsl:value-of select="successDegrees/success"/><xsl:text>  &#10;</xsl:text>
    </xsl:if>
    <xsl:if test="successDegrees/failure">
      <xsl:text>**Échec.** </xsl:text><xsl:value-of select="successDegrees/failure"/><xsl:text>&#10;</xsl:text>
    </xsl:if>
    <xsl:if test="successDegrees/criticalFailure">
      <xsl:text>**Échec critique.** </xsl:text><xsl:value-of select="successDegrees/criticalFailure"/><xsl:text>&#10;</xsl:text>
    </xsl:if>

    <!-- Spécial -->
    <xsl:if test="special">
      <xsl:text>**Spécial.** </xsl:text><xsl:value-of select="special"/><xsl:text>&#10;</xsl:text>
    </xsl:if>

    <!-- Activités conférées (style bloc inline, comme les capacités passives des monstres) -->
    <xsl:for-each select="grantedActivity">
      <xsl:text>&#10;</xsl:text>
      <xsl:text>**</xsl:text><xsl:value-of select="name"/><xsl:text>**</xsl:text>
      <xsl:if test="actions">
        <xsl:text> &#96;[</xsl:text>
        <xsl:call-template name="action-label">
          <xsl:with-param name="n" select="actions"/>
        </xsl:call-template>
        <xsl:text>]&#96;</xsl:text>
      </xsl:if>
      <xsl:if test="frequency">
        <xsl:text> **Fréquence.** </xsl:text><xsl:value-of select="frequency"/>
      </xsl:if>
      <xsl:if test="trigger">
        <xsl:text> **Déclencheur.** </xsl:text><xsl:value-of select="trigger"/>
      </xsl:if>
      <xsl:if test="requirement">
        <xsl:text> **Conditions.** </xsl:text><xsl:value-of select="requirement"/>
      </xsl:if>
      <xsl:text> </xsl:text><xsl:value-of select="description"/><xsl:text>&#10;</xsl:text>
    </xsl:for-each>

    <xsl:text>&#96;&#96;&#96;&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
