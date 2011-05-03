<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xsl:version="1.0">
  <xsl:template match="/">
    <evaluation>

      <title><xsl:value-of select=".//h3/span[2]"/></title>

      <instructions>
          <xsl:apply-templates select=".//div[@class='instruction']/node()"/>
      </instructions>

      <questions>
        <xsl:copy-of select=".//input[@type='hidden']"/>
        <xsl:apply-templates select=".//form/node()"/>
      </questions>

      <submitButton>
        <xsl:variable name="input" select=".//div[@class='act']/input[@type='submit']"/>
        <input type="submit" name="{$input/@name}" value="Submit"/>
      </submitButton>

      <state>
        <xsl:variable name="alertMessage" select=".//div[@class='alertMessage']/text()"/>
        <xsl:choose>
          <xsl:when test="contains($alertMessage, 'currently unpublished')">unpublished</xsl:when>
          <xsl:when test="starts-with($alertMessage, 'Sorry!')">closed</xsl:when>
          <xsl:when test="starts-with($alertMessage, 'You do not')">forbidden</xsl:when>
          <xsl:otherwise>open</xsl:otherwise>
        </xsl:choose>
      </state>

      <state_message>
        <xsl:choose>
          <xsl:when test=".//div[@class='messageAlert']">
            <xsl:value-of select=".//div[@class='messageAlert']/ul/li/span"/>
          </xsl:when>
          <xsl:when test=".//div[@class='alertMessage']/text()">
            <xsl:value-of select=".//div[@class='alertMessage']/text()"/>
          </xsl:when>
        </xsl:choose>          
      </state_message>

      <require_auth>
        <xsl:choose>
          <xsl:when test=".//*[@class='loginform']">true</xsl:when>
          <xsl:otherwise>false</xsl:otherwise>
        </xsl:choose>
      </require_auth>

    </evaluation>
  </xsl:template>

  <xsl:template match="@style"/>
  <xsl:template match="div[@class='act']"/>
  <xsl:template match="input[@type='hidden']"/>

  <xsl:template match="div[starts-with(@class, 'fake-fieldset')]">
    <div class="form-section">
      <h2><xsl:copy-of select="div/div[@class='legend']/text()"/></h2>
      <dl class="content-list">
        <xsl:for-each select="div/ol/li">
          <xsl:choose>
           <xsl:when test=".//*[@style='display:inline']/text()">
              <dt>
                <xsl:if test="div/div[@class='validFail']">
                  <xsl:attribute name="class">sakai-validation-error</xsl:attribute>
                </xsl:if>
                <xsl:copy-of select=".//*[@style='display:inline']/text()"/>
                <xsl:if test="div/div[@class='compulsory'] | div/div[@class='validFail']">
                  <xsl:text> </xsl:text><span class="sakai-compulsory-question">*</span>
                </xsl:if>
              </dt>
            </xsl:when>
            <xsl:otherwise>
              <dt>
                <xsl:apply-templates select="div/div/node()"/>
              </dt>
            </xsl:otherwise>
          </xsl:choose>
          <dd>
            <xsl:choose>
              <xsl:when test=".//div/table">
                <xsl:apply-templates select=".//div/table"/>
              </xsl:when>
              <xsl:when test="div/div[@class='compulsory'] | div/div[@class='validFail']">
                <xsl:apply-templates select="div/div[not(@class='JSevalComment')]/*[not(self::input[@type='hidden'])][last()]"/>
              </xsl:when>
              <xsl:when test="div/div[not(@class='JSevalComment' or @style='display:inline')]/*[not(self::input[@type='hidden'])][last()]">
                <xsl:copy-of select="div/div[not(@class='JSevalComment' or @style='display:inline')]/*[not(self::input[@type='hidden'])][last()]"/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:copy-of select="div[not(@style='display:inline')]/*[not(self::input[@type='hidden'])][last()]"/>
              </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="comment-field"/>
          </dd>
        </xsl:for-each>
      </dl>
    </div>
  </xsl:template>

  <xsl:template match="div[div/ul[contains(@class, ' mult-choice-ans')]] | div[ul[contains(@class, ' mult-choice-ans')]]">
    <ul>
      <xsl:for-each select=".//ul/li">
        <li>
          <xsl:if test="span[@class='na']">
            <xsl:attribute name="class">sakai-not-applicable</xsl:attribute>
          </xsl:if>
          <xsl:copy-of select=".//label/input"/>
          <xsl:text> </xsl:text>
          <label>
            <xsl:attribute name="for"><xsl:value-of select=".//label/input/@id"/></xsl:attribute>
            <xsl:value-of select=".//label/span/text()"/>
          </label>
        </li>
      </xsl:for-each>
    </ul>
  </xsl:template>

  <xsl:template match="table[@class='itemScalePanel']">
    <table>
      <tbody>
        <tr>
          <th><xsl:value-of select="normalize-space(.//td[contains(@class, 'compactDisplayStartGeneric')])"/></th>
          <xsl:choose>
            <xsl:when test=".//div[@class='scaleChoiceColored']/*">
              <xsl:for-each select=".//div[@class='scaleChoiceColored']/label/input">
                <td>
                  <input type="radio">
                    <xsl:copy-of select="@name"/>
                    <xsl:copy-of select="@value"/>
                    <xsl:copy-of select="@checked"/>
                  </input>
                </td>
              </xsl:for-each>
            </xsl:when>
            <xsl:when test=".//div[@class='scaleChoiceNotColored']">
              <xsl:for-each select=".//div[@class='scaleChoiceNotColored']/label/input">
                <td>
                  <input type="radio">
                    <xsl:copy-of select="@name"/>
                    <xsl:copy-of select="@value"/>
                    <xsl:copy-of select="@checked"/>
                  </input>
                </td>
              </xsl:for-each>
            </xsl:when>
          </xsl:choose>
          <th><xsl:value-of select="normalize-space(.//td[contains(@class, 'compactDisplayEndGeneric')])"/></th>
        </tr>
        <xsl:if test=".//td[contains(@class, ' na')]">
          <tr>
            <td class="sakai-not-applicable">
              <xsl:attribute name="colspan">
                <xsl:value-of select="count(.//label/input) + 2"/>
              </xsl:attribute>
              <xsl:copy-of select=".//td[contains(@class, ' na')]/input"/>
              <xsl:copy-of select=".//td[contains(@class, ' na')]/label"/>
            </td>
          </tr>
        </xsl:if>
      </tbody>
    </table>
  </xsl:template>

  <xsl:template match="div[@class='JSevalComment']" />

  <xsl:template name="comment-field">
    <xsl:if test="div/div[@class='JSevalComment']">
    <div class="sakai-comment-field">
      <xsl:variable name='id' select="div/div[@class='JSevalComment']//textarea/@name"/>
      <label>
        <xsl:attribute name="for">
          <xsl:value-of select="$id"/>
        </xsl:attribute>
        <xsl:text>Comment:</xsl:text>
      </label>
        <xsl:text> (optional)</xsl:text>
      <textarea>
        <xsl:attribute name="name"><xsl:value-of select="$id"/></xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="$id"/></xsl:attribute>
        <xsl:value-of select="div/div[@class='JSevalComment']//textarea/text()"/>
      </textarea>
      <xsl:copy-of select=".//textarea"/>
    </div>
    </xsl:if>
  </xsl:template>

  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()" />
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
